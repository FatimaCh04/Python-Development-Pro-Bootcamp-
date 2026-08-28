# 🔐 Day 88 — User Authentication System

A secure and responsive **User Authentication Web Application** built with **Python, Flask, Flask-Login, SQLAlchemy, SQLite, and Bootstrap**.

This project is part of my **100 Days of Python** journey and focuses on implementing user registration, login, logout, password hashing, session management, and protected routes.

---

## 🚀 Project Overview

The **SecureAuth** application provides a complete authentication workflow for a Flask web application.

Users can create an account, securely log in, access protected content, and log out of their session.

The project demonstrates how authentication can be integrated into a Python web application using Flask and a relational database.

---

## ✨ Features

* 👤 User registration
* 🔐 Secure login system
* 🔑 Password hashing
* 🚪 Logout functionality
* 🛡️ Protected routes
* 🔄 Session management
* 📧 Email-based user identification
* 💾 SQLite database storage
* ⚡ Flask backend
* 📱 Responsive interface
* 🚨 Login and registration validation
* 💬 User-friendly flash messages

---

## 🛠️ Technologies Used

| Technology           | Purpose                               |
| -------------------- | ------------------------------------- |
| **Python**           | Core programming language             |
| **Flask**            | Web framework                         |
| **Flask-Login**      | Authentication and session management |
| **Flask-SQLAlchemy** | Database ORM                          |
| **SQLite**           | User data storage                     |
| **Werkzeug**         | Password hashing                      |
| **Jinja2**           | HTML templating                       |
| **Bootstrap 5**      | Responsive UI                         |
| **HTML5**            | Page structure                        |
| **CSS3**             | Custom styling                        |

---

## 🏗️ Application Architecture

```text
                    User
                     │
                     ▼
              Flask Web App
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    Authentication          Protected
       Routes                 Routes
          │                     │
          ▼                     ▼
     Flask-Login          @login_required
          │
          ▼
     SQLAlchemy ORM
          │
          ▼
      SQLite DB
```

---

## 📂 Project Structure

```text
Day-88-Authentication/
│
├── main.py
├── requirements.txt
├── README.md
│
├── instance/
│   └── users.db
│
├── static/
│   └── css/
│       └── styles.css
│
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    └── secret.html
```

> `users.db` is automatically created when the application runs.

---

## 🔐 Authentication Flow

### 1. Registration

A new user provides:

* Name
* Email
* Password

The password is hashed before being stored in the database.

```text
User Registration
       ↓
Validate Input
       ↓
Hash Password
       ↓
Save User
       ↓
SQLite Database
       ↓
Login User
```

---

### 2. Login

The user enters their email and password.

The application:

1. Searches for the account.
2. Retrieves the stored password hash.
3. Verifies the entered password.
4. Creates an authenticated session.
5. Redirects the user to the protected dashboard.

```text
Login Form
    ↓
Find User
    ↓
Verify Password
    ↓
Create Session
    ↓
Protected Dashboard
```

---

### 3. Protected Route

The dashboard uses:

```python
@login_required
```

Only authenticated users can access it.

Unauthenticated users are redirected to the login page.

---

### 4. Logout

When the user logs out, their authentication session is removed and they are returned to the home page.

---

## 🔒 Password Security

Passwords are **never stored as plain text**.

The application uses Werkzeug password hashing:

```python
generate_password_hash()
```

During login, the submitted password is checked using:

```python
check_password_hash()
```

This provides a safer approach than storing raw passwords.

---

## 🗄️ Database Model

The `User` model contains:

| Field      | Type    | Description          |
| ---------- | ------- | -------------------- |
| `id`       | Integer | Unique user ID       |
| `name`     | String  | User's name          |
| `email`    | String  | Unique email address |
| `password` | String  | Hashed password      |

---

## 🌐 Application Pages

### 🏠 Home

Introduces the authentication application and provides login/register options.

### 📝 Register

Allows new users to create an account.

### 🔑 Login

Allows existing users to authenticate.

### 🔐 Dashboard

A protected page accessible only after successful authentication.

### 🚪 Logout

Ends the authenticated session.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-88-Authentication
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```powershell
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

Start the Flask server:

```bash
python main.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

---

## 🧪 Testing

### Test Registration

1. Open the application.
2. Click **Register**.
3. Enter a name, email, and password.
4. Submit the form.
5. Verify that the user reaches the protected dashboard.

### Test Login

1. Logout.
2. Open **Login**.
3. Enter the registered credentials.
4. Verify successful authentication.

### Test Incorrect Password

Enter an incorrect password and verify that an error message appears.

### Test Protected Route

After logging out, manually visit:

```text
http://127.0.0.1:5000/secret
```

The application should redirect the user to the login page.

### Test Duplicate Email

Try registering another account using the same email address.

The application should prevent duplicate accounts.

---

## 🧠 Key Concepts Practiced

This project strengthened my understanding of:

* Flask routing
* User authentication
* Flask-Login
* Login sessions
* Protected routes
* `@login_required`
* Password hashing
* Password verification
* SQLAlchemy models
* SQLite databases
* Form handling
* GET and POST requests
* Jinja2 templates
* Flash messages
* HTTP redirects
* Virtual environments

---

## 📚 Learning Outcomes

Through this project, I learned how to build a complete authentication workflow:

```text
Registration
     ↓
Password Hashing
     ↓
Database Storage
     ↓
Login
     ↓
Session Management
     ↓
Protected Content
     ↓
Logout
```

This provides a strong foundation for developing larger Flask applications that require secure user accounts.

---

## 🔮 Future Improvements

Potential improvements include:

* 📧 Email verification
* 🔄 Forgot password functionality
* 🔑 Password reset
* 👤 User profile management
* 🛡️ Two-factor authentication
* 👥 Role-based access control
* 🔒 Stronger password requirements
* 🚦 Login attempt limiting
* ☁️ Production database
* 🚀 Deployment
* 🔐 Environment variables for secrets

---

## 📦 Requirements

The project dependencies are listed in `requirements.txt`:

```text
Flask
Flask-SQLAlchemy
Flask-Login
Werkzeug
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## 🐍 100 Days of Python

### Day 88 / 100 — Completed ✅

This project is part of my **100 Days of Python** learning journey.

Day 88 focused on building a practical **Flask Authentication System** and understanding how authentication, password security, sessions, databases, and protected routes work together.

---

## 👩‍💻 Author

**Fatima Ch**

### 100 Days of Python 🐍

**Day 88/100 — Learn • Build • Improve 🚀**

---

## 📌 Project Status

**Completed ✅**

A fully functional Flask authentication application with:

* Registration
* Login
* Logout
* Password hashing
* Session management
* Protected routes
* SQLite database integration
