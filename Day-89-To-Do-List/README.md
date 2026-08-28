# 📝 Day 89 — To-Do List Web Application

A modern and responsive **To-Do List Web Application** built with **Python, Flask, Flask-SQLAlchemy, SQLite, HTML, CSS, and Bootstrap**.

This project was developed as part of my **100 Days of Python** journey and focuses on building a practical web application with database integration and CRUD functionality.

---

## 🚀 Project Overview

**TaskFlow** is a simple productivity application that allows users to create, manage, update, and organize their daily tasks.

The application stores tasks permanently in a **SQLite database**, allowing users to access their tasks even after restarting the application.

---

## ✨ Features

* ➕ Add new tasks
* ✏️ Edit existing tasks
* ✅ Mark tasks as completed
* 🔄 Toggle task completion status
* 🗑️ Delete tasks
* 🧹 Clear all completed tasks
* 📊 View total, pending, and completed tasks
* 💾 Persistent SQLite database storage
* 📱 Responsive design
* 🎨 Clean and modern interface
* ⚡ Fast Flask-based backend

---

## 🛠️ Technologies Used

| Technology           | Purpose                   |
| -------------------- | ------------------------- |
| **Python**           | Core programming language |
| **Flask**            | Web framework             |
| **Flask-SQLAlchemy** | Database ORM              |
| **SQLite**           | Database                  |
| **Jinja2**           | Dynamic HTML templates    |
| **HTML5**            | Web structure             |
| **CSS3**             | Styling                   |
| **Bootstrap 5**      | Responsive UI             |

---

## 📂 Project Structure

```text
Day-89-To-Do-List/
│
├── main.py
├── requirements.txt
├── README.md
│
├── instance/
│   └── todo.db
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

> `todo.db` is automatically created when the application runs for the first time.

---

## 🗄️ Database Structure

The application uses a `Todo` model containing:

| Field         | Type     | Description        |
| ------------- | -------- | ------------------ |
| `id`          | Integer  | Unique task ID     |
| `title`       | String   | Task title         |
| `description` | Text     | Task details       |
| `completed`   | Boolean  | Completion status  |
| `created_at`  | DateTime | Task creation date |

---

## 🔄 Application Workflow

```text
User
  ↓
Flask Web Application
  ↓
Routes
  ↓
SQLAlchemy ORM
  ↓
SQLite Database
  ↓
Jinja2 Templates
  ↓
Web Interface
```

---

## 📌 CRUD Operations

The project demonstrates the fundamental **CRUD** operations:

### Create

Users can create new tasks through the Add Task form.

### Read

All saved tasks are retrieved from the SQLite database and displayed on the dashboard.

### Update

Users can edit task titles and descriptions and change completion status.

### Delete

Users can permanently remove individual tasks or clear completed tasks.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day-89-To-Do-List
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

## ▶️ Running the Application

Start the Flask development server:

```bash
python main.py
```

The application will run at:

```text
http://127.0.0.1:5000
```

Open the address in your browser to use the application.

---

## 🧪 Testing the Application

After launching the application, test the following:

### Add Task

1. Click **Add Task**
2. Enter a task title
3. Add an optional description
4. Click **Create Task**

### Complete Task

Click the circular checkbox beside a task to mark it as completed.

### Edit Task

Click **Edit**, update the information, and save the changes.

### Delete Task

Click **Delete** and confirm the deletion.

### Clear Completed

Use **Clear Completed** to remove all completed tasks.

---

## 🎯 Learning Objectives

This project helped strengthen my understanding of:

* Flask application development
* Flask routing
* GET and POST requests
* HTML forms
* Jinja2 template inheritance
* SQLAlchemy ORM
* SQLite database integration
* CRUD operations
* Database models
* Dynamic content rendering
* HTTP redirects
* `url_for()`
* Responsive web design
* Virtual environments
* Python package management

---

## 🧠 Key Concepts

One of the main concepts practiced in this project was connecting a Flask application with a relational database:

```text
Python
   ↓
Flask
   ↓
SQLAlchemy
   ↓
SQLite
   ↓
Database
```

This provides a strong foundation for developing larger database-driven web applications.

---

## 🔮 Future Improvements

Possible future enhancements include:

* 🔐 User authentication
* 👤 Multiple user accounts
* 📅 Task deadlines
* 🔔 Task reminders
* 🏷️ Task categories
* 🔎 Search and filtering
* ⭐ Task priorities
* 📊 Productivity analytics
* 🌙 Dark mode
* ☁️ Cloud database integration
* 🚀 Deployment to a production server

---

## 📚 100 Days of Python

**Day 89 / 100 — Completed ✅**

This project represents another step in my journey of learning Python and building practical applications with Flask.

Through this project, I practiced combining **Python backend logic, database management, HTML templates, and responsive frontend design** into a complete web application.

---

## 👩‍💻 Author

**Fatima Ch**

### 100 Days of Python 🐍

**Day 89/100 — Keep Learning. Keep Building. Keep Improving. 🚀**

---

## ⭐ Project Status

**Completed ✅**

A fully functional Flask-based To-Do List application with SQLite database integration and CRUD functionality.
