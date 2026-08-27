# 🎵 The Musical Time Machine

> **Day 78 | 100 Days of Code — The Complete Python Pro Bootcamp**

A Python automation project that transforms a date into a personalized **Spotify playlist of Billboard Hot 100 songs** from that time.

The application combines **web scraping, API integration, OAuth authentication, and automation** to recreate the music of a specific date with a single input.

---

## 📌 Overview

The Musical Time Machine allows users to enter any historical date and automatically creates a Spotify playlist containing the Billboard Hot 100 tracks from that date.

### Workflow

**Date → Billboard Hot 100 → Web Scraping → Spotify Search → Playlist Creation**

---

## ✨ Key Features

- 📅 Search Billboard Hot 100 charts by date
- 🌐 Extract chart data using web scraping
- 🎧 Search tracks through the Spotify Web API
- 🔐 Authenticate securely using Spotify OAuth
- 📋 Automatically create a private Spotify playlist
- ➕ Add matched tracks to the playlist
- ⚡ Fully automated workflow

---

## 🛠️ Tech Stack

| Technology | Role |
|---|---|
| Python | Application logic |
| Requests | HTTP requests |
| BeautifulSoup | Billboard web scraping |
| Spotipy | Spotify API integration |
| Spotify Web API | Track search & playlist management |
| python-dotenv | Environment variable management |

---

## 📂 Project Structure

```text
Day-78-Musical-Time-Machine/
│
├── main.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md