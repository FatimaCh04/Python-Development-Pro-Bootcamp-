# 📚 Day 81 — Student Task & Study Planner

A modern **Student Task & Study Planner** built with **Python, Flask, SQLite, and SQLAlchemy**. This project provides a centralized platform for organizing study tasks, managing deadlines, setting priorities, and tracking academic progress.

## 📌 Project Overview

Managing multiple assignments, study sessions, and academic deadlines can be challenging. The **Student Task & Study Planner** provides a simple and practical solution for organizing study-related tasks in one place.

Users can create tasks, assign subjects, set deadlines and priorities, add notes, mark tasks as completed, and quickly search or filter their task list.

The project demonstrates how a Python Flask application can be integrated with a relational database to create a functional CRUD-based web application.

## ✨ Features

* **Task Management** — Create, view, update, and delete study tasks.
* **Subject Organization** — Associate each task with a specific subject.
* **Deadline Tracking** — Set deadlines for individual study tasks.
* **Priority Management** — Categorize tasks as High, Medium, or Low priority.
* **Task Completion** — Mark tasks as completed and undo completion when necessary.
* **Search** — Search tasks by title or subject.
* **Filtering** — Filter tasks by priority and completion status.
* **Dashboard Statistics** — View total, pending, completed, and high-priority tasks.
* **Notes** — Add additional information or study notes to each task.
* **Persistent Storage** — Store task data using SQLite.
* **Responsive Design** — Bootstrap-based interface suitable for desktop and mobile screens.

## 🛠️ Technologies Used

| Technology       | Purpose                    |
| ---------------- | -------------------------- |
| Python           | Core programming language  |
| Flask            | Web application framework  |
| Flask-SQLAlchemy | Flask database integration |
| SQLAlchemy       | Object-Relational Mapping  |
| SQLite           | Local relational database  |
| HTML5            | Web page structure         |
| CSS3             | Custom styling             |
| Bootstrap 5      | Responsive user interface  |
| Jinja2           | Dynamic template rendering |

## 🗂️ Project Structure

```text
Day81-Study-Planner/
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

The SQLite database is automatically created when the application is initialized.

## 🗄️ Database Model

The application uses a `StudyTask` model with the following fields:

```text
StudyTask
│
├── id
├── title
├── subject
├── deadline
├── priority
├── status
└── notes
```

## 🔄 CRUD Functionality

The application implements the complete CRUD workflow:

### Create

Add a new study task with its subject, deadline, priority, and notes.

### Read

View all saved tasks from the dashboard.

### Update

Modify existing task information whenever required.

### Delete

Remove tasks that are no longer needed.

## 🔎 Search & Filtering

The dashboard provides flexible task organization through:

* Search by task title
* Search by subject
* Filter by priority
* Filter by task status

This makes it easier to focus on specific academic tasks.

## 📊 Dashboard Statistics

The dashboard automatically displays:

* **Total Tasks**
* **Pending Tasks**
* **Completed Tasks**
* **High-Priority Tasks**

These statistics provide a quick overview of current study workload.

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day81-Study-Planner
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Application

```bash
python app.py
```

### 5. Open in Browser

```text
http://127.0.0.1:5000
```

The database will be generated automatically when the application runs.

## 🎯 Learning Objectives

This project helped strengthen my understanding of:

* Flask application development
* Flask routing
* GET and POST requests
* HTML forms
* Jinja2 templating
* SQLAlchemy ORM
* SQLite database integration
* CRUD operations
* Database querying and filtering
* Dynamic web pages
* Bootstrap responsive design
* Organizing a Flask project into templates and static files

## 🔐 Application Workflow

```text
User
  │
  ▼
Dashboard
  │
  ├── Add Task
  │      └── Save to SQLite
  │
  ├── View Tasks
  │
  ├── Search / Filter
  │
  ├── Mark Complete
  │
  ├── Edit Task
  │
  └── Delete Task
```

## 🚀 Future Improvements

Possible future enhancements include:

* User authentication and personal accounts
* Calendar-based deadline management
* Study session scheduling
* Automatic deadline reminders
* Progress charts and analytics
* Subject-wise progress tracking
* Recurring study tasks
* Dark mode
* Export tasks to CSV or PDF
* Cloud database integration

## 📚 100 Days of Python

**Day 81 of 100 Days of Python**

This project represents another milestone in my Python development journey. It combines **Python web development, Flask, database management, SQLAlchemy, CRUD operations, and responsive UI design** into a practical student productivity application.

## 👩‍💻 Author

**Fatima Ch**

---

⭐ If you find this project useful, consider starring the repository.
