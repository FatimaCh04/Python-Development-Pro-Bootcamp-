from flask import Flask, render_template, request
from news_fetcher import fetch_news, CATEGORIES

app = Flask(__name__)


@app.route("/")
def index():
    category = request.args.get("category", "technology")
    query = request.args.get("q", "").strip()

    articles = fetch_news(category=category, query=query)

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES,
        selected_category=category,
        query=query,
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    articles = fetch_news(
        category="technology",
        query=query
    )

    return render_template(
        "index.html",
        articles=articles,
        categories=CATEGORIES,
        selected_category="technology",
        query=query,
    )


if __name__ == "__main__":
    app.run(debug=True)