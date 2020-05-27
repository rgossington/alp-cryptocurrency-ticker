from datetime import datetime, timedelta
import time
import error
from coin import Coin


@error.handle_connection_error
def get_coins_list(coingecko, dashboard_conn=None):
    # Wraps the CoinGeckoApi method in a connection error handler. dashboard_conn is used in the wrapper.
    return coingecko.get_coins_list()


@error.close_db_conn_on_error
def update_db_coin_data(coins, db_conn):
    # Updates the db. NOTE: in_message will not be updated as this is controlled by the dashboard.
    # Will only update existing currencies. Add currencies using add_currency()

    # Re-check coins in db, in case any have been deleted
    coin_ids_that_exist = get_coin_ids(db_conn)

    for coin in coins:
        if coin.get_id() in coin_ids_that_exist:
            sql = "UPDATE coin_data SET symbol = ?, price = ?, price_previous = ?, last_updated = ? " \
                  "WHERE id = ?;"

            db_conn.execute(sql, (coin.get_symbol(), coin.get_price(), coin.get_price_previous(),
                                  coin.get_last_updated(), coin.get_id()))

    db_conn.commit()


@error.close_db_conn_on_error
def save_to_db_price_log(db_conn):
    timestamp = datetime.utcnow()
    cursor = db_conn.execute("SELECT id, symbol, price FROM coin_data;")

    for row in cursor:
        sql = "INSERT INTO price_log (timestamp, id, symbol, price) VALUES (?, ?, ?, ?);"
        db_conn.execute(sql, (timestamp, row[0], row[1], row[2]))

    db_conn.commit()


@error.close_db_conn_on_error
def read_coins_from_db(db_conn, coins=None):
    # Returns a list of coin instances from the db.
    # If we have already initialised a coin (in the coins list) then it will just update it rather than overwrite

    if coins is None:
        coins = []

    coins_return = []  # Separate list to make sure we don't return deleted coins
    cursor = db_conn.execute("SELECT id, symbol, price, price_previous, in_message, last_updated FROM coin_data")
    rows = cursor.fetchall()

    for row in rows:
        add_new_coin = True
        coin_id = row[0]
        symbol = row[1]
        price = row[2]
        price_previous = row[3]
        in_message = row[4]
        last_updated = row[5]

        # Check if we already have the coin and update if we do. Prevents losing price_previous.
        for coin in coins:
            if coin.get_id() == coin_id:
                add_new_coin = False

                coin.set_symbol(symbol)
                coin.set_price(price, price_previous)
                coin.set_in_message(in_message)
                coin.set_last_updated(last_updated)
                coins_return.append(coin)
                break

        if add_new_coin:
            coins_return.append(Coin(coin_id, symbol=symbol, price=price, price_previous=price_previous,
                                     in_message=in_message, last_updated=last_updated))

    return coins_return


@error.close_db_conn_on_error
def generate_print_str(coins, db_conn, override_message=None):
    # Generates the string to be printed. Eg "BTC-123.456"
    # And writes this message to the message_log db table

    print_str = ""
    separator = " "

    if override_message is not None and len(override_message) > 0:
        print_str = override_message
    else:
        for coin in coins:
            if coin.get_in_message() and coin.get_symbol() is not None and coin.get_price() is not None:
                symbol = coin.get_symbol().upper()
                price = round_to_string(coin.get_price())
                print_str += f"{symbol}-{price}{separator}"

        if len(print_str) > 0:
            print_str = print_str[:-len(separator)]     # Remove last separator

    timestamp = datetime.utcnow()
    sql = "INSERT INTO message_log (timestamp, message) VALUES (?, ?);"
    db_conn.execute(sql, (timestamp, print_str))
    db_conn.commit()

    return print_str


def round_to_string(value):
    # Rounds float, integers and numeric strings to 2dp and returns a string.
    # Be aware that the standard 'bankers rounding' is used (ie round half to even)

    if not isinstance(value, float):
        try:
            value = float(value)
        except TypeError:
            raise TypeError("value must be a float, int or numeric string.")

    return "%.2f" % round(value, 2)


def sleep_with_interrupt(socket_conn, update_interval, override_message):
    # Sleeps for the update_interval time.
    # Allows the sleep to be broken with a dashboard message

    for s in range(update_interval):
        if socket_conn is not None and socket_conn.poll():
            try:
                msg = socket_conn.recv()
            except:
                msg = ""

            if msg == "UPDATE_PRICES":
                break
            if isinstance(msg, dict) and "ticker_message" in msg:
                override_message = msg["ticker_message"]
                break

        time.sleep(1)

    return override_message


@error.close_db_conn_on_error
def add_currency(new_currency_id, db_conn):
    # Add a new currency entry to the db, if it doesn't already exist

    coin_ids = get_coin_ids(db_conn)
    if new_currency_id in coin_ids:     # checks if it is already in the db
        return None

    if len(new_currency_id) > 0 and isinstance(new_currency_id, str):
        sql = f"INSERT INTO coin_data (id, in_message) VALUES (?, ?);"
        db_conn.execute(sql, (new_currency_id, False))
        db_conn.commit()


@error.close_db_conn_on_error
def change_in_message(currency_id, value, db_conn):
    # Changes the in_message column for the specified coin
    sql = f"UPDATE coin_data SET in_message = ? WHERE id = ?;"
    db_conn.execute(sql, (value, currency_id))
    db_conn.commit()


@error.close_db_conn_on_error
def delete_currency(currency_id, db_conn):
    # Deletes a currency from the db
    sql = f"DELETE FROM coin_data WHERE id=(?);"
    db_conn.execute(sql, (currency_id,))
    db_conn.commit()


def request_price_update(dashboard_conn):
    # Send a message from the dashboard, to the ticker updater
    dashboard_conn.send("UPDATE_PRICES")


def get_next_update_string(coins, update_interval, dashboard_conn=None):
    # Determines when the next update is due

    if len(coins) > 0 and isinstance(coins[0].get_last_updated(), datetime):
        last_updated = coins[0].get_last_updated()
        next_update = last_updated + timedelta(seconds=update_interval)
        next_update_str = datetime.strftime(next_update, "%H:%M:%S")
    else:
        next_update_str = "N/A"

    # Connection error alert
    if dashboard_conn is not None and dashboard_conn.poll():
        try:
            msg = dashboard_conn.recv()
        except:
            msg = ""

        if msg == "CONNECTION_ERROR":
            next_update_str = "Connection error, attempting to re-connect"

    return next_update_str


@error.close_db_conn_on_error
def read_message_log(db_conn, message_log_limit, timestamp_format):
    # Reads the message log from the db. message_log_limit set in app.py

    sql = "SELECT timestamp, message FROM message_log ORDER BY timestamp DESC LIMIT ?;"
    cursor = db_conn.execute(sql, (message_log_limit,))

    # Read cursor and convert timestamp into the required string format
    message_data = []
    for row_t in cursor:
        row = list(row_t)
        row[0] = datetime.strftime(row[0], timestamp_format)
        message_data.append(row)

    return message_data


@error.close_db_conn_on_error
def save_prices_to_db(db_conn):
    # Saves all current coins into the price log table

    timestamp = datetime.utcnow()
    coins = read_coins_from_db(db_conn)

    for coin in coins:
        sql = "INSERT INTO price_log (timestamp, id, symbol, price) VALUES (?, ?, ?, ?)"
        db_conn.execute(sql, (timestamp, coin.get_id(), coin.get_symbol(), coin.get_price()))

    db_conn.commit()


@error.close_db_conn_on_error
def get_coin_ids(db_conn):
    # Returns a list of coin ids in the db

    sql = "SELECT id FROM coin_data;"
    cursor = db_conn.execute(sql)
    coin_ids = [row[0] for row in cursor]

    return coin_ids
