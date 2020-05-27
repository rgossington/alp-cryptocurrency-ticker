import requests


class CoinGeckoApi:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()

    def _base_request(self, url):
        response = requests.get(self.base_url + url)
        response.raise_for_status()     # Raise exceptions for 4xx (client error) and 5xx (server error) code responses
        return response.json()

    def get_coins_list(self):
        url = "/coins/list"
        return self._base_request(url)

    def get_simple_price(self, coin_id, vs_currency):
        url = f"/simple/price?ids={coin_id}&vs_currencies={vs_currency}"
        price_dict = self._base_request(url)

        try:
            price = price_dict[coin_id][vs_currency]
        except KeyError:
            return None

        return price
