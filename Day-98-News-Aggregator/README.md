# 📰 Day 98 — Automated News Aggregator

A modern **Python and Flask-based Automated News Aggregator** that collects the latest stories from RSS news feeds and presents them through a clean, responsive web dashboard.

The project demonstrates practical web development, HTTP requests, RSS/XML processing, HTML parsing, search functionality, category filtering, and responsive frontend design.

---

## 🚀 Features

* 📰 Automated news collection
* 🌐 Multiple RSS news sources
* 🔎 Keyword-based news search
* 🗂️ News category filtering
* 💻 Responsive web dashboard
* 🔗 Direct links to original articles
* 📅 Publication date display
* 🧹 Duplicate article removal
* ⚠️ Graceful request/error handling
* ✨ Animated article cards
* 📱 Mobile-friendly interface

---

## 🗂️ Available Categories

The application supports:

* Technology
* Business
* Science
* Sports
* Health
* World

---

## 🛠️ Technology Stack

### Backend

* Python
* Flask
* Requests
* BeautifulSoup
* lxml

### Frontend

* HTML5
* CSS3
* JavaScript
* Jinja2

### Data Source

* RSS/XML news feeds

---

## 📁 Project Structure

```text
Day-98-News-Aggregator/
│
├── app.py
├── news_fetcher.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   └── index.html
│
└── static/
    ├── style.css
    └── script.js
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
```

Move into the project directory:

```bash
cd Day-98-News-Aggregator
```

---

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv venv
```

Activate it using PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell activation is unavailable, you can run:

```powershell
venv\Scripts\activate.bat
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the Flask server:

```bash
python app.py
```

The application will normally be available at:

```text
http://127.0.0.1:5000
```

Open that address in your browser.

---

## 🔍 How It Works

The application follows a simple news aggregation pipeline:

```text
RSS News Feeds
      ↓
HTTP Request
      ↓
XML/RSS Parsing
      ↓
Article Extraction
      ↓
Duplicate Removal
      ↓
Search / Category Filtering
      ↓
Flask
      ↓
Responsive Web Dashboard
```

---

## 🔎 Search

Users can enter keywords into the search box.

For example:

```text
AI
Python
technology
space
football
```

The application searches article titles and descriptions and displays matching results.

---

## 🗂️ Category Filtering

Users can switch between different categories from the navigation bar.

Each category uses appropriate RSS feeds and displays the latest available stories.

---

## 🛡️ Error Handling

The application includes protection against common network and parsing failures.

If an RSS source becomes unavailable, the application continues running and displays an appropriate empty state instead of crashing.

---

## 🎯 Learning Objectives

This project demonstrates practical experience with:

* Flask routing
* Jinja2 templates
* HTTP requests
* RSS feeds
* XML parsing
* BeautifulSoup
* Web scraping concepts
* Search and filtering
* Error handling
* Responsive CSS
* JavaScript DOM manipulation
* Python modular programming

---

## 🔮 Future Improvements

Possible enhancements include:

* User accounts
* Favorite articles
* Saved news
* Dark mode
* Pagination
* News images
* Personalized news feeds
* Database storage
* Background scheduled updates
* AI-powered news summaries
* Sentiment analysis
* Email newsletter generation
* REST API integration

---

## 📌 Important Note

This project is intended for educational purposes.

News content belongs to its respective publishers. The application retrieves publicly available RSS information and links users to the original articles.

---

## 🎓 100 Days of Python

**Day 98 / 100**

This project represents another milestone in my Python development journey, focusing on real-world web applications, external data sources, automated data collection, and responsive user interfaces.

### Built With

**Python • Flask • Requests • BeautifulSoup • HTML • CSS • JavaScript**

---

## 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 98/100**

> Learn • Build • Practice • Improve 🚀
