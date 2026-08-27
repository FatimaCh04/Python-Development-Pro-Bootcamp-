import os
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv


# ============================================================
# DAY 78 - THE MUSICAL TIME MACHINE
# ============================================================

load_dotenv()

# ------------------------------------------------------------
# Spotify credentials
# ------------------------------------------------------------

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv(
    "SPOTIFY_REDIRECT_URI",
    "http://127.0.0.1:8888/callback"
)

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError(
        "Spotify credentials are missing. "
        "Please add them to your .env file."
    )


# ------------------------------------------------------------
# Get date from user
# ------------------------------------------------------------

date = input(
    "Which year do you want to travel to? "
    "Type the date in YYYY-MM-DD format: "
)

# Example:
# 2000-08-27


# ------------------------------------------------------------
# Scrape Billboard Hot 100
# ------------------------------------------------------------

billboard_url = (
    f"https://www.billboard.com/charts/hot-100/{date}/"
)

response = requests.get(
    billboard_url,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

if response.status_code != 200:
    print(
        f"Could not access Billboard chart. "
        f"Status code: {response.status_code}"
    )
    exit()


soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ------------------------------------------------------------
# Get song titles
# ------------------------------------------------------------

song_elements = soup.select(
    "li ul li h3"
)

song_names = [
    song.get_text(strip=True)
    for song in song_elements
]

# Remove duplicates while preserving order
song_names = list(dict.fromkeys(song_names))

if not song_names:
    print(
        "No songs were found. "
        "Try another date."
    )
    exit()


print(
    f"\nFound {len(song_names)} songs "
    f"from Billboard Hot 100."
)

print("\nFirst 10 songs:")

for song in song_names[:10]:
    print(song)


# ============================================================
# SPOTIFY
# ============================================================

# ------------------------------------------------------------
# Authenticate with Spotify
# ------------------------------------------------------------

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope="playlist-modify-private",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cache_path=".spotify_cache"
    )
)


# ------------------------------------------------------------
# Find songs on Spotify
# ------------------------------------------------------------

song_uris = []

for song in song_names:

    try:

        result = sp.search(
            q=f"track:{song}",
            type="track",
            limit=1
        )

        tracks = result["tracks"]["items"]

        if tracks:
            uri = tracks[0]["uri"]
            song_uris.append(uri)

    except Exception as error:

        print(
            f"Could not find '{song}': {error}"
        )


print(
    f"\nFound {len(song_uris)} songs on Spotify."
)


# ------------------------------------------------------------
# Get Spotify user ID
# ------------------------------------------------------------

current_user = sp.current_user()

user_id = current_user["id"]


# ------------------------------------------------------------
# Create playlist
# ------------------------------------------------------------

playlist_name = (
    f"{date} Billboard Hot 100"
)

playlist = sp.user_playlist_create(
    user=user_id,
    name=playlist_name,
    public=False,
    description=(
        f"Billboard Hot 100 songs from {date}. "
        f"Created with Python."
    )
)


playlist_id = playlist["id"]


# ------------------------------------------------------------
# Add songs to playlist
# ------------------------------------------------------------

if song_uris:

    # Spotify allows adding tracks in batches.
    for i in range(0, len(song_uris), 100):

        batch = song_uris[i:i + 100]

        sp.playlist_add_items(
            playlist_id=playlist_id,
            items=batch
        )


print("\n========================================")
print("       MUSICAL TIME MACHINE")
print("========================================")

print(
    f"\nPlaylist created successfully!"
)

print(
    f"Playlist name: {playlist_name}"
)

print(
    f"Songs added: {len(song_uris)}"
)

print("\nEnjoy your trip through time! 🎵")