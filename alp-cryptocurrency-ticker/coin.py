import error
from datetime import datetime
import backend

not_found_string = "..."


class Coin:
    def __init__(self, coin_id, symbol=None, price=None, price_previous=None,
                 in_message=False, last_updated=None):
        # Declare
        self._symbol = None
        self._price = None
        self._price_change = None
        self._in_message = None
        self._last_updated = None

        self._symbol_str = None
        self._price_str = None
        self._checkbox_string = None

        # Set
        self._coin_id = coin_id
        self.set_last_updated(last_updated)

        self.set_symbol(symbol)
        self.set_in_message(in_message)

        self._price_previous = price_previous
        self.set_price(price, price_previous)

    # Refresh/retrieve methods
    def refresh(self, coin_info, coingecko, vs_currency, dashboard_conn=None):
        self.retrieve_symbol(coin_info)
        self.retrieve_price(coingecko, vs_currency, dashboard_conn=dashboard_conn)

    @error.handle_connection_error
    def retrieve_price(self, coingecko, vs_currency, dashboard_conn=None):
        self._last_updated = datetime.utcnow()
        self._price_previous = self._price
        price = coingecko.get_simple_price(self._coin_id, vs_currency)
        self.set_price(price)

    def retrieve_symbol(self, coin_info):
        # Only runs if necessary
        if self._symbol is None:
            for d in coin_info:
                if d["id"] == self._coin_id:
                    self._symbol = d["symbol"]
                    break

        self.set_symbol(self._symbol)

    # Set value methods
    def set_price(self, price, price_previous=None):
        if price_previous is not None:
            self._price_previous = price_previous

        self._price = price
        if self._price is not None:
            self._price_str = backend.round_to_string(self._price)
        else:
            self._price_str = not_found_string
        self._update_price_change()

    def set_symbol(self, symbol):
        self._symbol = symbol
        if self._symbol is None:
            self._symbol_str = not_found_string
        else:
            self._symbol_str = str(self._symbol)

    def set_in_message(self, in_message):
        self._in_message = in_message

        if in_message is True or in_message == 1:
            self._checkbox_string = "checked"
        else:
            self._checkbox_string = ""

    def set_last_updated(self, last_updated):
        self._last_updated = last_updated

    # Get value methods
    def get_id(self):
        return self._coin_id

    def get_price(self):
        return self._price

    def get_price_previous(self):
        return self._price_previous

    def get_price_change(self):
        return self._price_change

    def get_symbol(self):
        return self._symbol

    def get_in_message(self):
        return self._in_message

    def get_last_updated(self):
        return self._last_updated

    # Get string methods
    def get_price_str(self):
        return self._price_str

    def get_price_change_str(self):
        return self._price_change_str

    def get_symbol_str(self):
        return self._symbol_str

    def get_checkbox_str(self):
        return self._checkbox_string

    def get_price_colour_str(self):
        return self._price_colour

    # Other methods
    def _update_price_change(self):
        if self._price is None:
            self._price_change = None
            self._price_change_str = not_found_string
        elif self._price_previous is None:
            self._price_change = 0
            self._price_change_str = backend.round_to_string(self._price_change)
        else:
            self._price_change = self._price - self._price_previous
            self._price_change_str = backend.round_to_string(self._price_change)

        self._update_price_colour()

    def _update_price_colour(self):
        colour = "#cc9200"  # Dark yellow, visible on white background

        if self._price_change is not None:
            price_change_str = backend.round_to_string(self._price_change)
            price_change_rounded = float(price_change_str)

            if price_change_rounded < 0:
                colour = "red"
            if price_change_rounded > 0:
                colour = "green"

        self._price_colour = colour
