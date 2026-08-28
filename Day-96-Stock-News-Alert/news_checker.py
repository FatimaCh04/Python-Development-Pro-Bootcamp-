import requests


class NewsChecker:

    BASE_URL = (
        "https://newsapi.org/v2/everything"
    )

    def __init__(self, api_key, company_name):
        self.api_key = api_key
        self.company_name = company_name

    def get_news(self):

        params = {
            "q": self.company_name,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 3
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            raise RuntimeError(
                data.get(
                    "message",
                    "News API request failed."
                )
            )

        articles = data.get(
            "articles",
            []
        )

        results = []

        for article in articles[:3]:

            title = article.get(
                "title",
                "No headline"
            )

            description = article.get(
                "description",
                "No description available."
            )

            results.append(
                {
                    "title": title,
                    "description": description
                }
            )

        return results