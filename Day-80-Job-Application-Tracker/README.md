# Day 79 — Personal Expense Tracker

## 📌 Project Overview

The **Personal Expense Tracker** is a Flask-based web application that allows users to manage their daily expenses in one place.

Users can add new expenses, view all recorded expenses, edit existing records, delete individual expenses, and clear all expenses. The application stores the data permanently in a **SQLite database** using **SQLAlchemy**.

## 🚀 Features

* ➕ Add new expenses
* 👀 View all expenses
* ✏️ Edit existing expenses
* 🗑️ Delete individual expenses
* 🧹 Clear all expenses
* 💰 Automatically calculate total expenses
* 🏷️ Categorize expenses
* 📅 Store expense dates
* 💾 SQLite database storage
* 📱 Responsive Bootstrap interface

## 🛠️ Technologies Used

* **Python**
* **Flask**
* **Flask-SQLAlchemy**
* **SQLite**
* **SQLAlchemy**
* **HTML5**
* **Bootstrap 5**
* **Jinja2**

## 📂 Project Structure

```text
Day79-Expense-Tracker/
│
├── app.py
├── requirements.txt
│
├── instance/
│   └── expenses.db
│
└── templates/
    ├── index.html
    ├── add.html
    └── edit.html
```

> The `expenses.db` file is automatically created when the application runs for the first time.

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### 2. Open the project folder

```bash
cd Day79-Expense-Tracker
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

### 5. Open in your browser

```text
http://127.0.0.1:5000
```

## 💡 How It Works

The application uses Flask routes to handle different operations:

| Route          | Purpose              |
| -------------- | -------------------- |
| `/`            | Display all expenses |
| `/add`         | Add a new expense    |
| `/edit/<id>`   | Edit an expense      |
| `/delete/<id>` | Delete an expense    |
| `/clear`       | Delete all expenses  |

Expense records are stored using a SQLAlchemy model:

```text
Expense
├── id
├── title
├── amount
├── category
└── date
```

## 🎯 Learning Objectives

This project helps practice:

* Flask application structure
* Flask routing
* GET and POST requests
* HTML forms
* Jinja2 templating
* SQLAlchemy models
* SQLite database operations
* CRUD operations
* Bootstrap UI
* Dynamic data rendering
* URL parameters
* Database queries

## 🔄 CRUD Operations

The project implements complete CRUD functionality:

**Create** → Add an expense
**Read** → View expenses
**Update** → Edit an expense
**Delete** → Remove an expense

## 📸 Application

The application provides a simple dashboard where users can see their total spending and manage individual expense records.

## 📚 Day 79 Progress

**100 Days of Python — Day 79**

This project focuses on combining Python programming with web development and database management using Flask and SQLAlchemy.

## 👩‍💻 Author

**Fatima Ch**

### ⭐ If you like this project

Feel free to ⭐ the repository and use the project for learning and practice.
