# 🎵 Day 46 - Spotify Musical Time Machine

## 100 Days of Python - Angela Yu

This is my Day 46 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

Spotify Musical Time Machine.

The program asks the user for a date and creates
a Spotify playlist containing songs from the
Billboard Hot 100 chart for that date.

## ✨ How It Works

1. User enters a date.
2. Billboard Hot 100 data is retrieved.
3. Spotify authentication is performed.
4. Songs are searched on Spotify.
5. A new Spotify playlist is created.
6. Matching songs are added to the playlist.

## 📚 Topics Covered

- Web Scraping / Data Retrieval
- Requests
- Spotify API
- OAuth Authentication
- Spotipy
- API Searching
- List Comprehensions
- String Methods
- Date Handling
- Creating Spotify Playlists
- Adding Tracks to Playlists

## 🛠 Technologies

- Python
- Requests
- Spotipy
- Spotify Web API

## 📁 Project Structure

```text
Day-46-Spotify-Musical-Time-Machine/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 📦 Installation

Install the required packages:

```bash
pip install -r requirements.txt
```

## 🔑 Spotify Setup

Create an application in the Spotify
Developer Dashboard.

Add the redirect URI:

```text
http://127.0.0.1:8888/callback
```

Then add your credentials to the project.

Never upload your Spotify Client Secret
to GitHub.

## ▶️ Run

```bash
python main.py
```

Enter a date in:

```text
YYYY-MM-DD
```

Example:

```text
2010-08-15
```

## 🎵 Result

The program creates a Spotify playlist containing
the Billboard Hot 100 songs that could be found
on Spotify for the selected date.

## 📖 Learning Outcomes

Through Day 46 I learned how to:

- Work with APIs
- Authenticate with OAuth
- Use Spotipy
- Search Spotify tracks
- Retrieve track URIs
- Create Spotify playlists
- Add multiple tracks to playlists
- Work with external data sources

