# 🐍 Day 60 - Flask Blog with SQLite

## 100 Days of Python - Angela Yu

This is my Day 60 Flask project from my
100 Days of Python journey.

## 🎯 Project

A Flask blog application connected to a
SQLite database using Flask-SQLAlchemy.

## ✨ Features

- Flask web application
- SQLite database
- SQLAlchemy ORM
- Blog post model
- Dynamic post pages
- Database queries
- Jinja templates
- Bootstrap responsive UI
- About page
- Contact page

## 📚 Concepts Covered

- Flask
- SQLite
- Flask-SQLAlchemy
- Database Models
- Database Queries
- ORM
- `db.create_all()`
- `db.session`
- `commit()`
- Dynamic Routes
- Jinja
- Bootstrap

## 🛠 Technologies

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja
- Bootstrap
- HTML
- CSS

## 📁 Project Structure

```text
Day-60-Flask-Blog-Database/
│
├── main.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── post.html
│   ├── about.html
│   └── contact.html
│
└── static/
    └── style.css
```

## 📦 Installation

```bash
pip install -r requirements.txt
```

## ▶️ Run

```bash
python main.py
```

Open:

```text
http://127.0.0.1:5000
```

## 🗄️ Database

The application automatically creates:

```text
blog.db
```

The database contains a `BlogPost` table.

## 🌐 Routes

Home:

```text
/
```

About:

```text
/about
```

Contact:

```text
/contact
```

Individual posts:

```text
/post/1
/post/2
/post/3
```

## 🧠 Learning Outcomes

Through Day 60 I learned how to:

- Connect Flask with SQLite
- Create database models
- Use SQLAlchemy ORM
- Store blog posts
- Retrieve records from a database
- Create dynamic database-driven pages
- Handle missing records
- Combine Flask, Jinja and databases


