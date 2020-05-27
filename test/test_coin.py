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


class TestCoin(unittest.TestCase):
    def test_init(self):
        coin = Coin("bitcoin",
                    symbol="btc",
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_id(), "bitcoin")
        self.assertEqual(coin.get_symbol(), "btc")
        self.assertEqual(coin.get_price(), None)
        self.assertEqual(coin.get_price_previous(), None)
        self.assertEqual(coin.get_price_change(), None)
        self.assertEqual(coin.get_in_message(), True)
        self.assertEqual(coin.get_last_updated(), None)

    def test_update_price_change(self):
        coin = Coin("bitcoin",
                    symbol="btc",
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        coin._price = 123.123
        coin._price_previous = 123
        coin._update_price_change()
        self.assertAlmostEqual(coin._price_change, 0.123)
        self.assertEqual(coin._price_change_str, "0.12")
        self.assertEqual(coin._price_colour, "green")

        coin._price = 123.123
        coin._price_previous = None
        coin._update_price_change()
        self.assertEqual(coin._price_change, 0)
        self.assertEqual(coin._price_change_str, "0.00")
        self.assertNotEqual(coin._price_colour, "green")
        self.assertNotEqual(coin._price_colour, "red")

        coin._price = None
        coin._price_previous = None
        coin._update_price_change()
        self.assertEqual(coin._price_change, None)
        self.assertEqual(coin._price_change_str, "...")
        self.assertNotEqual(coin._price_colour, "green")
        self.assertNotEqual(coin._price_colour, "red")

    def test_update_price_colour(self):
        coin = Coin("bitcoin",
                    symbol="btc",
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        coin._price_change = 0.1
        coin._update_price_colour()
        self.assertEqual(coin._price_colour, "green")

        coin._price_change = -0.1
        coin._update_price_colour()
        self.assertEqual(coin._price_colour, "red")

        coin._price_change = 0
        coin._update_price_colour()
        self.assertNotEqual(coin._price_colour, "green")
        self.assertNotEqual(coin._price_colour, "red")

        coin._price_change = None
        coin._update_price_colour()
        self.assertNotEqual(coin._price_colour, "green")
        self.assertNotEqual(coin._price_colour, "red")

    def test_set_price(self):
        coin = Coin("bitcoin",
                    symbol="btc",
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        coin.set_price(123.123)
        self.assertEqual(coin._price, 123.123)
        self.assertEqual(coin._price_str, "123.12")
        self.assertEqual(coin._price_change, 0)

        coin.set_price(123.123, 123)
        self.assertEqual(coin._price, 123.123)
        self.assertEqual(coin._price_str, "123.12")
        self.assertAlmostEqual(coin._price_change, 0.123)
        self.assertEqual(coin._price_change_str, "0.12")

    def test_set_symbol(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        coin.set_symbol(None)
        self.assertEqual(coin._symbol, None)
        self.assertEqual(coin._symbol_str, "...")

        coin.set_symbol("btc")
        self.assertEqual(coin._symbol, "btc")
        self.assertEqual(coin._symbol_str, "btc")

    def test_set_in_message(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        coin.set_in_message(None)
        self.assertEqual(coin._in_message, None)
        self.assertEqual(coin._checkbox_string, "")

        coin.set_in_message(False)
        self.assertEqual(coin._in_message, False)
        self.assertEqual(coin._checkbox_string, "")

        coin.set_in_message(True)
        self.assertEqual(coin._in_message, True)
        self.assertEqual(coin._checkbox_string, "checked")

    def test_set_last_updated(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        coin.set_last_updated(datetime(2020, 5, 26, 13, 0, 0))
        self.assertEqual(coin._last_updated, datetime(2020, 5, 26, 13, 0, 0))

    def test_get_id(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_id(), "bitcoin")

    def test_get_price(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=123.123,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_price(), 123.123)

    def test_get_price_previous(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=125.125,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_price_previous(), 125.125)

    def test_get_price_change(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=123,
                    price_previous=123.1,
                    in_message=True,
                    last_updated=None)

        self.assertAlmostEqual(coin.get_price_change(), -0.1)

    def test_get_symbol(self):
        coin = Coin("bitcoin",
                    symbol="btc",
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_symbol(), "btc")

    def test_get_in_message(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_in_message(), True)

    def test_get_last_updated(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=datetime(2020, 5, 26, 13, 0, 0))

        self.assertEqual(coin.get_last_updated(), datetime(2020, 5, 26, 13, 0, 0))

    def test_get_price_str(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=123.123,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_price_str(), "123.12")

    def test_get_price_change_str(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=123.123,
                    price_previous=123,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_price_change_str(), "0.12")

    def test_get_symbol_str(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_symbol_str(), "...")

    def test_get_checkbox_str(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=None,
                    price_previous=None,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_checkbox_str(), "checked")

    def test_get_price_colour_str(self):
        coin = Coin("bitcoin",
                    symbol=None,
                    price=123.123,
                    price_previous=123,
                    in_message=True,
                    last_updated=None)

        self.assertEqual(coin.get_price_colour_str(), "green")

    def test_retrieve_price(self):
        coin = Coin("bitcoin")
        vs_currency = "usd"

        coin.retrieve_price(coingecko, vs_currency)

        self.assertEqual(type(coin._last_updated), datetime)
        self.assertEqual(coin._price_previous, None)
        self.assertEqual(type(coin._price), float)
        self.assertGreater(coin._price, 0)
        self.assertEqual(type(coin._price_str), str)
        self.assertEqual(coin._price_change, 0)

        price_previous_expected = coin._price
        coin.retrieve_price(coingecko, vs_currency)

        self.assertEqual(type(coin._last_updated), datetime)
        self.assertEqual(coin._price_previous, price_previous_expected)
        self.assertEqual(type(coin._price), float)
        self.assertGreater(coin._price, 0)
        self.assertEqual(type(coin._price_str), str)
        self.assertEqual(type(coin._price_change), float)

    def test_retrieve_symbol(self):
        coin_info = backend.get_coins_list(coingecko)

        coin = Coin("bitcoin")
        coin.retrieve_symbol(coin_info)
        self.assertEqual(coin._symbol, "btc")

        coin = Coin("testing123")
        coin.retrieve_symbol(coin_info)
        self.assertEqual(coin._symbol, None)

    def test_refresh(self):
        coin_info = backend.get_coins_list(coingecko)
        vs_currency = "usd"

        coin = Coin("bitcoin")
        coin.refresh(coin_info, coingecko, vs_currency)

        self.assertEqual(type(coin._price), float)
        self.assertEqual(coin._symbol, "btc")


if __name__ == "__main__":
    unittest.main()
