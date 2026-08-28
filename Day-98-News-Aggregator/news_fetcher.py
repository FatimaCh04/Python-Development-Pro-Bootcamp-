import requests
import html
from bs4 import BeautifulSoup
from datetime import datetime


CATEGORIES = {
    "technology": "technology",
    "business": "business",
    "science": "science",
    "sports": "sports",
    "health": "health",
    "world": "world",
}


RSS_FEEDS = {
    "technology": [
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    ],
    "business": [
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    ],
    "science": [
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    ],
    "sports": [
        "https://feeds.bbci.co.uk/sport/rss.xml",
    ],
    "health": [
        "https://feeds.bbci.co.uk/news/health/rss.xml",
    ],
    "world": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
    ],
}


def clean_text(text):
    """Remove HTML and unnecessary whitespace."""

    if not text:
        return ""

    text = html.unescape(text)

    soup = BeautifulSoup(text, "html.parser")

    return " ".join(soup.get_text(" ").split())


def format_date(date_string):
    """Convert RSS date into a readable format."""

    if not date_string:
        return "Recently"

    try:
        parsed_date = datetime.strptime(
            date_string[:25],
            "%a, %d %b %Y %H:%M:%S"
        )

        return parsed_date.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return date_string[:30]


def parse_feed(url, category):
    """Fetch and parse an RSS feed."""

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Day-98-News-Aggregator/1.0"
            },
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.content, "xml")

        articles = []

        for item in soup.find_all("item")[:10]:
            title = clean_text(
                item.title.get_text() if item.title else ""
            )

            link = (
                item.link.get_text(strip=True)
                if item.link
                else "#"
            )

            description = clean_text(
                item.description.get_text()
                if item.description
                else "No description available."
            )

            pub_date = (
                item.pubDate.get_text(strip=True)
                if item.pubDate
                else ""
            )

            if not title:
                continue

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "link": link,
                    "date": format_date(pub_date),
                    "category": category.title(),
                }
            )

        return articles

    except requests.RequestException:
        return []

    except Exception:
        return []


def fetch_news(category="technology", query=""):
    """Fetch news from multiple RSS sources."""

    if category not in RSS_FEEDS:
        category = "technology"

    all_articles = []

    for feed_url in RSS_FEEDS[category]:
        articles = parse_feed(feed_url, category)
        all_articles.extend(articles)

    # Remove duplicate article titles.
    unique_articles = []
    seen_titles = set()

    for article in all_articles:
        normalized_title = article["title"].lower().strip()

        if normalized_title not in seen_titles:
            seen_titles.add(normalized_title)
            unique_articles.append(article)

    # Search filtering.
    if query:
        search_term = query.lower()

        unique_articles = [
            article
            for article in unique_articles
            if search_term in article["title"].lower()
            or search_term in article["description"].lower()
        ]

    return unique_articles[:20]