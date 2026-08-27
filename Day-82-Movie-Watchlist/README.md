# 🎬 Day 82 — Movie Watchlist Manager

A professional web-based **Movie Watchlist Manager** built with **Python, Flask, SQLite, and SQLAlchemy**. The application allows users to organize their movie collection, track watched and unwatched titles, manage ratings, and quickly search or filter their watchlist.

---

## 📌 Project Overview

Managing a growing list of movies can become difficult when titles, ratings, genres, and viewing status are stored in different places.

The **Movie Watchlist Manager** provides a centralized platform for managing this information. Users can add movies, update their details, mark movies as watched, search the watchlist, and filter movies based on genre or viewing status.

This project demonstrates the integration of **Flask web development with SQLite database management and SQLAlchemy ORM**.

---

## ✨ Features

* 🎬 **Movie Management** — Add, edit, and delete movies.
* ⭐ **Rating System** — Store ratings from 0 to 10.
* 🎭 **Genre Organization** — Categorize movies by genre.
* 📅 **Release Year** — Record the movie's release year.
* ✅ **Watch Status** — Mark movies as Watched or Unwatched.
* 🔎 **Search** — Search movies by title or genre.
* 🏷️ **Filtering** — Filter movies by genre and watch status.
* 📊 **Dashboard Statistics** — View total movies, watched movies, unwatched movies, and average rating.
* 📝 **Notes** — Add personal notes to individual movies.
* 💾 **Persistent Storage** — Store data using SQLite.
* 📱 **Responsive UI** — Bootstrap-based interface for different screen sizes.

---

## 🛠️ Technologies Used

| Technology           | Purpose                    |
| -------------------- | -------------------------- |
| **Python**           | Core programming language  |
| **Flask**            | Web application framework  |
| **Flask-SQLAlchemy** | Flask database integration |
| **SQLAlchemy**       | Object-Relational Mapping  |
| **SQLite**           | Database storage           |
| **HTML5**            | Application structure      |
| **CSS3**             | Custom styling             |
| **Bootstrap 5**      | Responsive UI              |
| **Jinja2**           | Dynamic template rendering |

---

## 🗂️ Project Structure

```text
Day82-Movie-Watchlist/
│
├── app.py
├── requirements.txt
│
├── static/
│   └── css/
│       └── styles.css
│
└── templates/
    ├── base.html
    ├── index.html
    ├── add.html
    └── edit.html
```

The `movies.db` SQLite database is automatically generated when the application is initialized.

---

## 🗄️ Database Model

The application uses a `Movie` model containing the following fields:

```text
Movie
│
├── id
├── title
├── genre
├── year
├── rating
├── status
└── notes
```

### Field Description

| Field    | Description               |
| -------- | ------------------------- |
| `id`     | Unique movie identifier   |
| `title`  | Movie title               |
| `genre`  | Movie category            |
| `year`   | Release year              |
| `rating` | Rating between 0 and 10   |
| `status` | Watched or Unwatched      |
| `notes`  | Additional personal notes |

---

## 🔄 CRUD Operations

The application implements complete **CRUD functionality**.

### Create

Add a new movie with its title, genre, release year, rating, and notes.

### Read

Display all saved movies on the main dashboard.

### Update

Edit movie information whenever required.

### Delete

Remove movies from the watchlist.

---

## 🔍 Search & Filtering

The application provides multiple ways to organize the watchlist:

* Search by movie title
* Search by genre
* Filter by genre
* Filter by Watched/Unwatched status

This allows users to quickly find specific movies.

---

## 📊 Dashboard

The dashboard provides an overview of the movie collection:

* **Total Movies**
* **Watched Movies**
* **Movies To Watch**
* **Average Rating**

These statistics are calculated dynamically from the SQLite database.

---

## 🔄 Application Workflow

```text
                  ┌─────────────────┐
                  │    Dashboard    │
                  └────────┬────────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Add Movie      Search/Filter   Statistics
             │
             ▼
       SQLite Database
             │
      ┌──────┼──────┐
      │      │      │
      ▼      ▼      ▼
     Edit   Watch   Delete
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day82-Movie-Watchlist
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

### 5. Open in Browser

```text
http://127.0.0.1:5000
```

The SQLite database will be created automatically on the first run.

---

## 🎯 Learning Objectives

This project helped strengthen my practical understanding of:

* Flask application development
* Flask routing
* GET and POST requests
* HTML form handling
* Jinja2 templating
* SQLAlchemy ORM
* SQLite database integration
* CRUD operations
* Database queries
* Search and filtering
* Dynamic dashboard statistics
* Bootstrap responsive design
* Structuring a Flask web application

---

## 🚀 Future Enhancements

Possible improvements for future versions include:

* 🎞️ Movie poster integration
* 🔗 Integration with a movie API
* 👤 User authentication
* ❤️ Favorites and watch-later lists
* 📅 Personal watch dates
* 📈 Movie statistics and analytics
* 🎯 Personalized recommendations
* 📤 Export watchlist to CSV/PDF
* 🌙 Dark mode
* ☁️ Cloud database support

---

## 📚 100 Days of Python

**Day 82 of 100 Days of Python**

This project represents another milestone in my Python development journey, combining **Flask, SQLAlchemy, SQLite, CRUD operations, database management, search functionality, filtering, and responsive web design** into a practical application.

---

## 👩‍💻 Author

**Fatima Ch**

### ⭐ Project Status

**Completed — Day 82/100 ✅**

> Part of my ongoing **100 Days of Python** coding journey. 🐍💻
