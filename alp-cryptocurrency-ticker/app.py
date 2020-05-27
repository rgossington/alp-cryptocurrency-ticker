from flask import Flask, request, render_template, jsonify
from version import VERSION
import tickerupdater
from tickerupdater import update_interval, db_path, dashboard_conn_socket
import backend
import multiprocessing
from multiprocessing.connection import Listener
import sqlite3

app = Flask(__name__)
app_subdomain = "alp-crypocurrency-ticker"
app_name = "Alp Cryptocurrency Ticker"

timestamp_format = "%Y-%m-%d %H:%M:%S"
message_log_limit = 5000

multiprocessing.Process(target=tickerupdater.run).start()

# Direct socket communication between dashboard and tickerupdater
# Example outputs from dashboard are 'UPDATE_PRICES' (force update), message_override (str to broadcast on ticker)
# Example inputs to dashboard are 'CONNECTED', 'CONNECTION_ERROR'
address = ('localhost', dashboard_conn_socket)
listener = Listener(address)
dashboard_conn = listener.accept()                  # Must be placed after starting tickerupdater to accept connection


@app.route(f"/{app_subdomain}/", methods=["POST", "GET"])
def home():
    return render_template("dashboard.html", app_name=app_name, version=VERSION, app_subdomain=app_subdomain)


@app.route(f"/{app_subdomain}/save_prices", methods=["GET", "POST"])
def save_prices():
    if request.method == "POST":
        db_conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        backend.save_prices_to_db(db_conn)
        db_conn.close()

    return jsonify(success=True)


@app.route(f"/{app_subdomain}/message_control", methods=["GET", "POST"])
def message_control():
    if request.method == "POST":
        if "ticker_message" in request.values:
            ticker_message_dict = {"ticker_message": request.values["ticker_message"]}
            dashboard_conn.send(ticker_message_dict)

        return jsonify(success=True)

    return render_template("message_control.html")


@app.route(f"/{app_subdomain}/message_log")
def message_log():
    db_conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    message_data = backend.read_message_log(db_conn, message_log_limit, timestamp_format)
    db_conn.close()

    return render_template("message_log.html", message_data=message_data)


@app.route(f"/{app_subdomain}/price_viewer", methods=["GET", "POST"])
def price_viewer():
    db_conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    if request.method == "POST" and "case" in request.values:       # Case variable used to determine what to do
        if request.values["case"] == "UPDATE_PRICES":
            backend.request_price_update(dashboard_conn)

        if request.values["case"] == "ADD_CURRENCY":
            new_currency_id = request.values["new_currency_id"]
            new_currency_id = new_currency_id.lower()
            backend.add_currency(new_currency_id, db_conn)
            backend.request_price_update(dashboard_conn)

        if request.values["case"] == "CHANGE_IN_MESSAGE":
            currency_id = request.values["currency_id"].replace("'", "")
            checkbox_value = request.values["in_message_checked"] == "true"
            backend.change_in_message(currency_id, checkbox_value, db_conn)
            backend.request_price_update(dashboard_conn)

        if request.values["case"] == "DELETE_CURRENCY":
            currency_id = request.values["delete_currency_id"]
            was_in_message = request.values["in_message_checked"] == "checked"
            backend.delete_currency(currency_id, db_conn)

            if was_in_message:
                backend.request_price_update(dashboard_conn)

        db_conn.close()
        return jsonify(success=True)

    # Normal update
    coins = backend.read_coins_from_db(db_conn)
    next_update_str = backend.get_next_update_string(coins, update_interval, dashboard_conn)

    db_conn.close()
    return render_template("price_viewer.html", coins=coins, next_update_str=next_update_str)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
