from coingeckoapi import CoinGeckoApi
from multiprocessing.connection import Client
import sqlite3
import backend
import error

update_interval = 60
db_path = 'cryptocurrencyticker.db'
vs_currency = "usd"
dashboard_conn_socket = 6000


@error.loop_on_error
def run():
    db_conn = sqlite3.connect(db_path)

    # Socket connection to dashboard
    address = ('localhost', dashboard_conn_socket)
    dashboard_conn = Client(address)

    # General setup
    coingecko = CoinGeckoApi()
    coin_info = backend.get_coins_list(coingecko, dashboard_conn=dashboard_conn)  # available coin information
    coins = []
    override_message = None

    # Main loop
    while True:
        coins = backend.read_coins_from_db(db_conn, coins)  # adding/deleting coins is controlled by the dashboard
        for coin in coins:
            coin.refresh(coin_info, coingecko, vs_currency, dashboard_conn=dashboard_conn)

        backend.update_db_coin_data(coins, db_conn)
        print(backend.generate_print_str(coins, db_conn, override_message))

        # Listens for messages from dashboard during sleep
        override_message = backend.sleep_with_interrupt(dashboard_conn, update_interval, override_message)
