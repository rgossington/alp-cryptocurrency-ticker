from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
import time
import traceback
import sqlite3

timeout_minutes = 2    # 2 minutes
sleep_time = 10
attempt_limit = int((timeout_minutes * 60) / sleep_time)


def handle_connection_error(function):
    # Decorator to loop when there is a connection error. Will try to communicate CONNECTION_ERROR with dashboard.

    def wrapper(*args, **kwargs):
        # Try to get the socket connection with the dashboard
        dashboard_conn = None
        if "dashboard_conn" in kwargs:
            dashboard_conn = kwargs["dashboard_conn"]

        attempt_count = 0

        # Loop until connection is restored, or timeout reached
        while True:
            try:
                output = function(*args, **kwargs)
                send_alert_to_dashboard(dashboard_conn, "CONNECTED")    # Makes sure CONNECTION_ERROR is overwritten
                return output
            except (HTTPError, ConnectionError, Timeout):
                attempt_count += 1

                send_alert_to_dashboard(dashboard_conn, "CONNECTION_ERROR")
                print(f"Connection error. Reconnection attempt {attempt_count}/{attempt_limit}")

                if attempt_count >= attempt_limit:
                    raise RequestException(f"Connection could not be re-established after {timeout_minutes} minutes")
                time.sleep(sleep_time)

    return wrapper


def loop_on_error(function):
    # Generic decorator to loop/restart on uncaught exceptions

    def wrapper(*args, **kwargs):
        while True:
            try:
                function(*args, **kwargs)
            except:
                traceback.print_exc()
                time.sleep(sleep_time)
    return wrapper


def send_alert_to_dashboard(dashboard_conn, msg):
    # Sends msg to the dashboard if the connection instance has been passed
    if dashboard_conn is not None:
        dashboard_conn.send(msg)


def close_db_conn_on_error(function):
    # Wraps around db functions to close connections on error. Prevents db being locked on error

    def wrapper(*args, **kwargs):
        # get the connection from the function args and kwargs
        connection = None
        for arg in (args + tuple(kwargs.values())):
            if isinstance(arg, sqlite3.Connection):
                connection = arg
                break

        try:
            return function(*args, **kwargs)
        except Exception as e:
            if connection is not None:
                connection.close()
            raise e

    return wrapper
