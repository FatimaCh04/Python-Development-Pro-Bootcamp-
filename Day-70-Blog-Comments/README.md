# 📝 Blog Capstone — Day 70

A complete database-driven blog application with user
authentication and a commenting system.

This project continues the Blog Capstone by adding comments
to individual blog posts.

## 🚀 Features

- User registration
- Login and logout
- Password hashing
- Protected routes
- Create blog posts
- Edit posts
- Delete posts
- User/post relationships
- Comment system
- Add comments
- Display comments
- Comment authors
- Delete own comments
- Authorization
- SQLite database
- SQLAlchemy ORM
- Responsive interface

## 🛠️ Technologies

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- HTML
- CSS
- Bootstrap

## 📂 Structure

Day-70-Blog-Comments/

├── main.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── post.html
│   └── make-post.html
│
└── static/
    └── css/
        └── styles.css

## ⚙️ Installation

Create a virtual environment:

python -m venv venv

Activate on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run:

python main.py

Open:

http://127.0.0.1:5000

## 💬 Comment System

Authenticated users can open a blog post and submit a comment.

Each comment stores:

- Comment text
- Author ID
- Post ID

The database relationships connect:

User → Comments

Blog Post → Comments

## 🗄️ Database

The application contains three main tables:

### Users

- id
- name
- email
- password_hash

### Blog Posts

- id
- title
- subtitle
- body
- image_url
- created_at
- author_id

### Comments

- id
- text
- author_id
- post_id

## 🧪 Testing

1. Register a user.
2. Login.
3. Create a blog post.
4. Open the post.
5. Add a comment.
6. Logout.
7. Register another user.
8. Login as the second user.
9. Open the same post.
10. Add another comment.
11. Verify both comments appear.
12. Delete your own comment.

## 🎯 Learning Goals

This project demonstrates:

- Flask authentication
- Flask-Login
- SQLAlchemy relationships
- Foreign keys
- One-to-many relationships
- Database CRUD
- Protected routes
- Authorization
- User-generated content
