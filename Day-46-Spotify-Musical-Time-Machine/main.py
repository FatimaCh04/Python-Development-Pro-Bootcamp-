import requests
import json
from pathlib import Path


# ==========================================
# DAY 46 - MUSICAL TIME MACHINE
# Spotify Premium-Free Demo Version
# ==========================================


def get_billboard_songs(date):
    """
    Get Billboard Hot 100 songs for a given date.
    """

    url = (
        "https://raw.githubusercontent.com/"
        "mhollingshead/billboard-hot-100/main/"
        f"date/{date}.json"
    )

    response = requests.get(
        url,
        timeout=15
    )

    if response.status_code != 200:
        print(
            f"\n❌ Could not find Billboard data "
            f"for {date}."
        )
        return []

    data = response.json()

    return data.get("data", [])


def create_playlist_file(songs, date):
    """
    Create a local playlist file.
    """

    playlist_name = (
        f"{date} Billboard Hot 100"
    )

    playlist = {
        "name": playlist_name,
        "date": date,
        "source": "Billboard Hot 100",
        "songs": []
    }

    for position, song in enumerate(
        songs,
        start=1
    ):

        playlist["songs"].append(
            {
                "position": position,
                "title": song.get(
                    "song",
                    "Unknown Song"
                ),
                "artist": song.get(
                    "artist",
                    "Unknown Artist"
                )
            }
        )

    file_name = (
        f"playlist_{date}.json"
    )

    file_path = Path(file_name)

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            playlist,
            file,
            indent=4,
            ensure_ascii=False
        )

    return file_path


# ==========================================
# GET DATE
# ==========================================

date = input(
    "Which year do you want to travel to? "
    "Type the date in YYYY-MM-DD format: "
).strip()


# ==========================================
# VALIDATE DATE
# ==========================================

if len(date) != 10 or date[4] != "-" or date[7] != "-":

    print(
        "\n❌ Invalid date format."
    )

    print(
        "Please use YYYY-MM-DD."
    )

    exit()


# ==========================================
# GET BILLBOARD SONGS
# ==========================================

print(
    "\n🔎 Searching Billboard Hot 100..."
)

songs = get_billboard_songs(date)


if not songs:

    print(
        "\n❌ No songs found."
    )

    exit()


print(
    f"\n🎵 Found {len(songs)} songs!"
)


# ==========================================
# DISPLAY SONGS
# ==========================================

print(
    "\nBillboard Hot 100:"
)

print(
    "-" * 60
)


for position, song in enumerate(
    songs,
    start=1
):

    title = song.get(
        "song",
        "Unknown Song"
    )

    artist = song.get(
        "artist",
        "Unknown Artist"
    )

    print(
        f"{position}. {title} - {artist}"
    )


# ==========================================
# CREATE LOCAL PLAYLIST
# ==========================================

print(
    "\n💾 Creating local playlist..."
)

playlist_file = create_playlist_file(
    songs,
    date
)


# ==========================================
# SUCCESS
# ==========================================

print(
    "\n" + "=" * 60
)

print(
    "🎉 DAY 46 COMPLETE!"
)

print(
    "=" * 60
)

print(
    f"\n📁 Playlist saved as:"
)

print(
    f"   {playlist_file}"
)

print(
    "\nSpotify API was skipped because "
    "this is the Premium-free learning version."
)

print(
    "\nYou can open the JSON file and see "
    "all 100 songs from your selected date."
)