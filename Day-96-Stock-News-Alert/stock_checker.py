import requests


class StockChecker:

    BASE_URL = (
        "https://www.alphavantage.co/query"
    )

    def __init__(self, api_key, symbol):
        self.api_key = api_key
        self.symbol = symbol

    def get_price_change(self):

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": self.symbol,
            "outputsize": "compact",
            "apikey": self.api_key
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if "Note" in data:
            raise RuntimeError(
                "Alpha Vantage API rate limit reached."
            )

        if "Error Message" in data:
            raise RuntimeError(
                data["Error Message"]
            )

        time_series = data.get(
            "Time Series (Daily)"
        )

        if not time_series:
            raise RuntimeError(
                "No daily stock data returned."
            )

        dates = sorted(
            time_series.keys(),
            reverse=True
        )

        if len(dates) < 2:
            raise RuntimeError(
                "Not enough stock data available."
            )

        latest_date = dates[0]
        previous_date = dates[1]

        latest_close = float(
            time_series[latest_date]["4. close"]
        )

        previous_close = float(
            time_series[previous_date]["4. close"]
        )

        price_change = (
            latest_close - previous_close
        )

        percentage_change = (
            price_change
            / previous_close
            * 100
        )

        return price_change, percentage_change