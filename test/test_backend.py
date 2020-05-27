import unittest
import sys

sys.path.append("../alp-cryptocurrency-ticker/")

import backend
from coingeckoapi import CoinGeckoApi
from coin import Coin
import sqlite3
from datetime import datetime

db_path = 'test.db'
db_conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
coingecko = CoinGeckoApi()


class TestBackend(unittest.TestCase):
    def setUp(self):
        db_conn.execute("DELETE FROM coin_data;")
        db_conn.execute("DELETE FROM price_log;")
        db_conn.execute("DELETE FROM message_log;")
        db_conn.commit()

    def tearDown(self):
        db_conn.execute("DELETE FROM coin_data;")
        db_conn.execute("DELETE FROM price_log;")
        db_conn.execute("DELETE FROM message_log;")
        db_conn.commit()

    def test_get_coins_list(self):
        coin_list = backend.get_coins_list(coingecko)

        self.assertEqual(type(coin_list), list)
        self.assertEqual(type(coin_list[0]), dict)
        self.assertGreater(len(coin_list), 1000)

    def test_update_db_coin_data(self):
        # Insert 2 new rows
        coins = [None, None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.123,
                        price_previous=123,
                        in_message=False,
                        last_updated=datetime.utcnow())

        coins[1] = Coin("testing123",
                        symbol=None,
                        price=None,
                        price_previous=None,
                        in_message=False,
                        last_updated=datetime.utcnow())

        backend.add_currency("bitcoin", db_conn)
        backend.add_currency("testing123", db_conn)
        backend.update_db_coin_data(coins, db_conn)
        cursor = db_conn.execute("SELECT * FROM coin_data;")
        db_conn.commit()

        for index, row in enumerate(cursor):
            self.assertIn(row[0], coins[index].get_id())
            self.assertEqual(row[1], coins[index].get_symbol())
            self.assertEqual(row[2], coins[index].get_price())
            self.assertEqual(row[3], coins[index].get_price_previous())
            self.assertEqual(row[4], coins[index].get_in_message())
            self.assertEqual(type(row[5]), datetime)
            self.assertEqual(row[5], coins[index].get_last_updated())

        # Update row
        coins = [None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.2,
                        price_previous=123.123,
                        in_message=False,
                        last_updated=datetime.utcnow())

        backend.update_db_coin_data(coins, db_conn)
        cursor = db_conn.execute("SELECT * FROM coin_data;")
        db_conn.commit()

        rows = cursor.fetchall()

        self.assertEqual(rows[0][0], coins[0].get_id())
        self.assertEqual(rows[0][1], coins[0].get_symbol())
        self.assertEqual(rows[0][2], coins[0].get_price())
        self.assertEqual(rows[0][3], coins[0].get_price_previous())
        self.assertEqual(rows[0][4], coins[0].get_in_message())
        self.assertEqual(type(rows[0][5]), datetime)
        self.assertEqual(rows[0][5], coins[0].get_last_updated())

    def test_save_to_db_price_log(self):
        # Insert new rows
        coins = [None, None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.123,
                        price_previous=123,
                        in_message=False,
                        last_updated=datetime.utcnow())

        coins[1] = Coin("testing123",
                        symbol=None,
                        price=None,
                        price_previous=None,
                        in_message=False,
                        last_updated=datetime.utcnow())

        backend.update_db_coin_data(coins, db_conn)
        db_conn.commit()

        backend.save_to_db_price_log(db_conn)
        cursor = db_conn.execute("SELECT * FROM price_log;")

        for index, row in enumerate(cursor):
            self.assertEqual(type(row[0]), datetime)
            self.assertGreaterEqual(datetime.utcnow(), row[0])
            self.assertEqual(row[1], coins[index].get_id())
            self.assertEqual(row[2], coins[index].get_symbol())
            self.assertEqual(row[3], coins[index].get_price())

    def test_read_coins_from_db(self):
        # Read new coins
        coins = [None, None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.123,
                        price_previous=123,
                        in_message=False,
                        last_updated=datetime.utcnow())

        coins[1] = Coin("testing123",
                        symbol=None,
                        price=None,
                        price_previous=None,
                        in_message=False,
                        last_updated=datetime.utcnow())

        backend.add_currency("bitcoin", db_conn)
        backend.add_currency("testing123", db_conn)
        backend.update_db_coin_data(coins, db_conn)
        db_conn.commit()

        coins_read = backend.read_coins_from_db(db_conn, [])

        self.assertEqual(len(coins_read), len(coins))
        self.assertEqual(coins_read[0].get_id(), coins[0].get_id())
        self.assertEqual(coins_read[0].get_in_message(), coins[0].get_in_message())
        self.assertEqual(coins_read[0].get_symbol(), coins[0].get_symbol())
        self.assertEqual(coins_read[0].get_price(), coins[0].get_price())
        self.assertAlmostEqual(coins_read[0].get_price_change(), 0.123)
        self.assertEqual(coins_read[0].get_price_previous(), 123)
        self.assertEqual(coins_read[0].get_last_updated(), coins[0].get_last_updated())

        self.assertEqual(coins_read[1].get_id(), coins[1].get_id())
        self.assertEqual(coins_read[1].get_in_message(), coins[1].get_in_message())
        self.assertEqual(coins_read[1].get_symbol(), coins[1].get_symbol())
        self.assertEqual(coins_read[1].get_price(), coins[1].get_price())
        self.assertEqual(coins_read[1].get_price_change(), None)
        self.assertEqual(coins_read[1].get_last_updated(), coins[1].get_last_updated())

        # Read existing coins
        backend.update_db_coin_data(coins, db_conn)
        db_conn.commit()

        coins_read = backend.read_coins_from_db(db_conn, coins)

        self.assertEqual(len(coins_read), len(coins))
        self.assertEqual(coins_read[0].get_id(), coins[0].get_id())
        self.assertEqual(coins_read[0].get_in_message(), coins[0].get_in_message())
        self.assertEqual(coins_read[0].get_symbol(), coins[0].get_symbol())
        self.assertEqual(coins_read[0].get_price(), coins[0].get_price())
        self.assertEqual(coins_read[0].get_price_change(), coins[0].get_price_change())
        self.assertEqual(coins_read[0].get_last_updated(), coins[0].get_last_updated())

    def test_generate_print_str(self):
        print_str_expected = []

        # All enabled, one blank
        coins = [None, None, None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.123,
                        price_previous=123,
                        in_message=True,
                        last_updated=datetime.utcnow())

        coins[1] = Coin("tron",
                        symbol="trx",
                        price=0.978,
                        price_previous=0.978,
                        in_message=True,
                        last_updated=datetime.utcnow())

        coins[2] = Coin("testing123",
                        symbol=None,
                        price=None,
                        price_previous=None,
                        in_message=True,
                        last_updated=datetime.utcnow())

        print_str = backend.generate_print_str(coins, db_conn)
        print_str_expected.append("BTC-123.12 TRX-0.98")

        self.assertEqual(print_str, print_str_expected[0])

        cursor = db_conn.execute("SELECT * FROM message_log;")
        rows = [row for row in cursor]
        self.assertEqual(type(rows[0][0]), datetime)
        self.assertGreater(datetime.utcnow(), rows[0][0])
        self.assertEqual(rows[0][1], print_str_expected[0])

        # Disable one
        coins[0] = Coin("bitcoin")
        coins[0].set_in_message(False)

        print_str = backend.generate_print_str(coins, db_conn)
        print_str_expected.append("TRX-0.98")

        self.assertEqual(print_str, print_str_expected[1])

        cursor = db_conn.execute("SELECT * FROM message_log;")
        rows = [row for row in cursor]
        self.assertEqual(rows[0][1], print_str_expected[0])

        self.assertEqual(type(rows[1][0]), datetime)
        self.assertGreater(datetime.utcnow(), rows[1][0])
        self.assertEqual(rows[1][1], print_str_expected[1])

    def test_round_to_string(self):
        rounded_string = backend.round_to_string(1.2345)
        self.assertEqual(rounded_string, "1.23")

        rounded_string = backend.round_to_string(0.125)
        self.assertEqual(rounded_string, "0.12")

        rounded_string = backend.round_to_string(0.135)
        self.assertEqual(rounded_string, "0.14")

        rounded_string = backend.round_to_string(5)
        self.assertEqual(rounded_string, "5.00")

        rounded_string = backend.round_to_string("1.2345")
        self.assertEqual(rounded_string, "1.23")

        self.assertRaises(TypeError, backend.round_to_string, ["invalid"])

    def test_add_currency(self):
        # Add first
        backend.add_currency("bitcoin", db_conn)

        cursor = db_conn.execute("SELECT * FROM coin_data;")
        rows = cursor.fetchall()

        self.assertEqual(rows[0][0], "bitcoin")
        self.assertEqual(rows[0][1], None)
        self.assertEqual(rows[0][2], None)
        self.assertEqual(rows[0][3], None)
        self.assertEqual(rows[0][4], False)
        self.assertEqual(rows[0][5], None)

        # Add second
        backend.add_currency("tron", db_conn)

        cursor = db_conn.execute("SELECT * FROM coin_data;")
        rows = cursor.fetchall()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "tron")

        # Add existing
        backend.add_currency("tron", db_conn)
        self.assertEqual(len(rows), 2)

    def test_change_in_message(self):
        # Add and change
        backend.add_currency("bitcoin", db_conn)
        backend.change_in_message("bitcoin", True, db_conn)

        cursor = db_conn.execute("SELECT * FROM coin_data;")
        rows = cursor.fetchall()

        self.assertEqual(rows[0][0], "bitcoin")
        self.assertEqual(rows[0][4], True)

        # Change back
        backend.change_in_message("bitcoin", False, db_conn)

        cursor = db_conn.execute("SELECT * FROM coin_data;")
        rows = cursor.fetchall()

        self.assertEqual(rows[0][0], "bitcoin")
        self.assertEqual(rows[0][4], False)

    def test_delete_currency(self):
        # Add and delete
        backend.add_currency("bitcoin", db_conn)
        backend.delete_currency("bitcoin", db_conn)

        cursor = db_conn.execute("SELECT * FROM coin_data;")
        rows = cursor.fetchall()

        self.assertEqual(len(rows), 0)

    def test_get_next_update_string(self):
        update_interval = 60

        # Normal
        coins = [None, None]
        coins[0] = Coin("bitcoin",
                        last_updated=datetime(2020, 5, 26, 13, 0, 0))

        coins[1] = Coin("tron",
                        last_updated=datetime(2020, 5, 26, 13, 0, 0))

        next_update_string = backend.get_next_update_string(coins, update_interval)
        self.assertEqual(next_update_string, "13:01:00")

        # No coins
        coins = []
        next_update_string = backend.get_next_update_string(coins, update_interval)
        self.assertEqual(next_update_string, "N/A")

    def test_read_message_log(self):
        # Write to table
        coins = [None, None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.123,
                        price_previous=123,
                        in_message=True,
                        last_updated=datetime.utcnow())

        coins[1] = Coin("testing123",
                        symbol=None,
                        price=None,
                        price_previous=None,
                        in_message=True,
                        last_updated=datetime.utcnow())

        backend.generate_print_str(coins, db_conn)

        timestamp_format = "%H:%M:%S"
        message_data = backend.read_message_log(db_conn, 5000, timestamp_format)

        self.assertEqual(message_data[0][0].count(":"), 2)
        self.assertEqual(message_data[0][1], "BTC-123.12")

    def test_save_prices_to_db(self):
        # Set up new coins
        coins = [None, None]
        coins[0] = Coin("bitcoin",
                        symbol="btc",
                        price=123.123,
                        price_previous=123,
                        in_message=False,
                        last_updated=datetime.utcnow())

        coins[1] = Coin("testing123",
                        symbol=None,
                        price=None,
                        price_previous=None,
                        in_message=False,
                        last_updated=datetime.utcnow())

        backend.add_currency("bitcoin", db_conn)
        backend.add_currency("testing123", db_conn)
        backend.update_db_coin_data(coins, db_conn)
        db_conn.commit()

        # Save, read and check
        backend.save_prices_to_db(db_conn)

        cursor = db_conn.execute("SELECT * FROM price_log;")

        rows = cursor.fetchall()

        self.assertEqual(type(rows[0][0]), datetime)
        self.assertEqual(rows[0][1], "bitcoin")
        self.assertEqual(rows[0][2], "btc")
        self.assertEqual(rows[0][3], 123.123)

        self.assertEqual(type(rows[1][0]), datetime)
        self.assertEqual(rows[1][1], "testing123")
        self.assertEqual(rows[1][2], None)
        self.assertEqual(rows[1][3], None)

    def test_get_coin_ids(self):
        backend.add_currency("bitcoin", db_conn)
        backend.add_currency("testing123", db_conn)

        coin_ids = backend.get_coin_ids(db_conn)

        self.assertListEqual(coin_ids, ["bitcoin", "testing123"])


if __name__ == "__main__":
    unittest.main()
