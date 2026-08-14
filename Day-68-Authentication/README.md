# 🔐 Day 68 - Authentication

## 100 Days of Python - Angela Yu

A Flask authentication application built as part
of my 100 Days of Python journey.

The project demonstrates user registration,
secure password hashing, login/logout functionality,
and protected routes.

---

## ✨ Features

- User registration
- User login
- User logout
- Secure password hashing
- Password verification
- SQLite database
- SQLAlchemy ORM
- Flask-Login authentication
- Protected dashboard
- Session management
- Flash messages
- Responsive UI

---

## 🛠️ Technologies

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- Werkzeug
- HTML
- CSS
- Bootstrap

---

## 📁 Project Structure

```text
Day-68-Authentication/
│
├── main.py
├── requirements.txt
├── README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   └── secrets.html
│
└── static/
    └── css/
        └── style.css
```

---

## 🚀 Installation

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
```

Move into the project:

```bash
cd Day-68-Authentication
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
python main.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 🌐 Routes

### Home

```text
/
```

### Register

```text
/register
```

### Login

```text
/login
```

### Protected Dashboard

```text
/secrets
```

### Logout

```text
/logout
```

---

## 🔐 Authentication Flow

1. User creates an account.
2. Password is hashed.
3. User information is stored in SQLite.
4. User logs in.
5. Password hash is verified.
6. Flask-Login creates an authenticated session.
7. Protected pages become accessible.
8. User can log out and end the session.

---

## 📚 Concepts Learned

- Flask authentication
- Flask-Login
- User sessions
- `login_user()`
- `logout_user()`
- `login_required`
- `current_user`
- Password hashing
- Password verification
- SQLAlchemy models
- SQLite databases
- Flash messages
- Protected routes
- Jinja templates

---

## 🎯 Learning Outcome

This project helped me understand how authentication
works in a Flask web application and how to protect
routes from unauthenticated users.

---
