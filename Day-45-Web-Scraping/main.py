import requests
from bs4 import BeautifulSoup


URL = "https://www.empireonline.com/movies/features/best-movies-2/"


headers = {
    "User-Agent": "Mozilla/5.0"
}


response = requests.get(URL, headers=headers, timeout=15)

response.raise_for_status()


soup = BeautifulSoup(response.text, "html.parser")


# Find movie titles
movie_titles = soup.find_all("h2")


movies = []

for movie in movie_titles:

    title = movie.get_text(strip=True)

    if title:
        movies.append(title)


# Remove duplicates while keeping order
movies = list(dict.fromkeys(movies))


# Reverse the list so movie #1 comes first
movies.reverse()


with open("movies.txt", "w", encoding="utf-8") as file:

    for movie in movies:
        file.write(movie + "\n")


print(f"Successfully scraped {len(movies)} movie titles!")

print("\nMovies:")

for movie in movies:
    print(movie)