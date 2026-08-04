# 📝 DevBlog Platform

A modern, full-stack blogging platform built with **Flask** that allows users to register, log in, publish blog posts, edit or delete their own articles, upload profile pictures, and interact through comments.

---

## 📌 Features

### 🔐 User Authentication
- User Registration
- User Login & Logout
- Secure Password Hashing
- Session Management using Flask-Login

### 📝 Blog Management
- Create New Blog Posts
- View All Blog Posts
- Edit Your Own Posts
- Delete Your Own Posts
- Responsive Blog Cards

### 💬 Comment System
- Logged-in users can comment on posts
- Display comments under each blog post

### 👤 User Profile
- Update Profile Information
- Upload Profile Picture
- Dashboard with User Statistics

### 🎨 Modern UI
- Bootstrap 5 Responsive Design
- Mobile Friendly Layout
- Clean Navigation
- Flash Messages
- Dashboard Interface

---

## 🛠️ Tech Stack

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- WTForms
- SQLite
- Jinja2
- Bootstrap 5
- HTML5
- CSS3
- JavaScript

---

## 📂 Project Structure

```
DevBlog/
│
├── app.py
├── models.py
├── routes.py
├── forms.py
├── config.py
├── requirements.txt
│
├── instance/
│   └── blog.db
│
├── static/
│   ├── css/
│   ├── uploads/
│   └── images/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── create_post.html
│   ├── edit_post.html
│   ├── post.html
│   ├── dashboard.html
│   ├── 403.html
│   └── 404.html
│
└── README.md
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/FatimaCh04/Python-Development-Pro-Bootcamp-/tree/main/Blog-platform
cd devblog-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows**

```bash
venv\Scripts\activate
```


### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

---

## 📸 Screenshots



---

## 📚 Database

The project uses **SQLite** with SQLAlchemy ORM.

### Database Models

- User
- Post
- Comment

Relationships:

```
User
 ├── Posts
 └── Comments

Post
 └── Comments
```

---

## 🔒 Security

- Password Hashing
- Authentication using Flask-Login
- Login Required Routes
- User Authorization
- Form Validation
- Secure File Uploads

---

## 🎯 Future Improvements

- Like & Dislike System
- Categories & Tags
- Search Functionality
- Email Verification
- Password Reset
- Rich Text Editor
- Dark Mode
- Admin Panel

---

## 👨‍💻 Author

**Fatima**

Python & Flask Developer

