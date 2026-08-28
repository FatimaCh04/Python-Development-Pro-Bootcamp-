import requests
from bs4 import BeautifulSoup


URL = "https://www.empireonline.com/movies/features/best-movies-2/"


def get_movie_titles():
    print("=" * 60)
    print("          🎬 TOP 100 MOVIES WEB SCRAPER")
    print("=" * 60)

    print("\nConnecting to Empire Online...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            URL,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print("\n❌ Could not access the website.")
        print(f"Error: {error}")
        return []

    print("✅ Website downloaded successfully.")

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    movie_titles = []

    # Empire's movie list uses h2 headings
    headings = soup.find_all("h2")

    for heading in headings:

        title = heading.get_text(
            strip=True
        )

        if title:
            movie_titles.append(title)

    # Remove duplicates while keeping order
    unique_titles = []

    for title in movie_titles:

        if title not in unique_titles:
            unique_titles.append(title)

    return unique_titles


def save_movies(movie_titles):
    if not movie_titles:
        print("\n❌ No movie titles were found.")
        return

    with open(
        "movies.txt",
        "w",
        encoding="utf-8"
    ) as file:

        for index, movie in enumerate(
            movie_titles,
            start=1
        ):

            file.write(
                f"{index}. {movie}\n"
            )

    print(
        f"\n💾 Saved {len(movie_titles)} "
        "movie titles to movies.txt"
    )


def display_movies(movie_titles):
    if not movie_titles:
        return

    print("\n" + "=" * 60)
    print("                 MOVIES FOUND")
    print("=" * 60)

    for index, movie in enumerate(
        movie_titles,
        start=1
    ):

        print(
            f"{index:>3}. {movie}"
        )

    print("=" * 60)


def main():
    movies = get_movie_titles()

    if movies:
        display_movies(movies)
        save_movies(movies)

        print(
            "\n🎉 Web scraping completed successfully!"
        )


if __name__ == "__main__":
    main()