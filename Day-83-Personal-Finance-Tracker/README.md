# 💰 Day 83 — Personal Finance Tracker

A professional web-based **Personal Finance Tracker** developed with **Python, Flask, SQLite, and SQLAlchemy**. The application helps users manage their income and expenses, monitor their balance, organize transactions by category, and gain a clear overview of their financial activity.

---

## 📌 Project Overview

Managing personal finances effectively requires keeping track of income, expenses, and spending patterns.

The **Personal Finance Tracker** provides a centralized dashboard where users can record financial transactions, categorize them, review their spending, and monitor their overall balance.

The project demonstrates practical implementation of **Flask web development, database management, SQLAlchemy ORM, CRUD operations, search, filtering, and dynamic financial calculations**.

---

## ✨ Features

* 💵 **Income Management** — Record and manage income transactions.
* 💸 **Expense Management** — Track daily expenses.
* 🏷️ **Category Management** — Organize transactions by categories.
* 📅 **Date Tracking** — Record the date of every transaction.
* 📊 **Financial Dashboard** — View important financial statistics.
* 💰 **Balance Calculation** — Automatically calculate current balance.
* 🔎 **Search** — Search transactions by title or category.
* 🔍 **Filtering** — Filter transactions by category or transaction type.
* ✏️ **Edit Transactions** — Update existing financial records.
* 🗑️ **Delete Transactions** — Remove unwanted records.
* 📈 **Expense Breakdown** — View total expenses by category.
* 📝 **Transaction Notes** — Add additional details to transactions.
* 💾 **Persistent Storage** — Store financial records using SQLite.
* 📱 **Responsive Interface** — Bootstrap-based responsive design.

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
| **Bootstrap 5**      | Responsive user interface  |
| **Jinja2**           | Dynamic template rendering |

---

## 🗂️ Project Structure

```text
Day83-Personal-Finance-Tracker/
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

The `finance.db` SQLite database is automatically created when the application is initialized.

---

## 🗄️ Database Model

The application uses a `Transaction` model containing:

```text
Transaction
│
├── id
├── title
├── amount
├── transaction_type
├── category
├── date
└── notes
```

### Field Description

| Field              | Description                        |
| ------------------ | ---------------------------------- |
| `id`               | Unique transaction identifier      |
| `title`            | Name or description of transaction |
| `amount`           | Transaction amount                 |
| `transaction_type` | Income or Expense                  |
| `category`         | Financial category                 |
| `date`             | Transaction date                   |
| `notes`            | Additional transaction information |

---

## 🔄 CRUD Functionality

The application implements complete **CRUD operations**.

### Create

Add a new income or expense transaction with its amount, category, date, and notes.

### Read

View saved transactions and financial statistics from the dashboard.

### Update

Edit transaction information whenever required.

### Delete

Remove transactions from the database.

---

## 📊 Financial Dashboard

The dashboard dynamically calculates:

* **Total Income**
* **Total Expenses**
* **Current Balance**
* **Total Transactions**

The balance is calculated using:

```text
Balance = Total Income - Total Expenses
```

---

## 📈 Expense Breakdown

The application groups expense transactions by category and calculates the total amount spent in each category.

Example:

```text
Food          $250
Transport     $120
Education     $300
Shopping      $180
```

This provides a quick overview of spending patterns.

---

## 🔎 Search & Filtering

Users can easily organize financial records using:

* Search by transaction title
* Search by category
* Filter by category
* Filter by Income
* Filter by Expense

---

## 🔄 Application Workflow

```text
                    Dashboard
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
     Add Transaction  Search       Statistics
          │          / Filter
          ▼
    SQLite Database
          │
     ┌────┼────┐
     │    │    │
     ▼    ▼    ▼
   Edit Delete  View
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day83-Personal-Finance-Tracker
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

The SQLite database will be created automatically when the application starts.

---

## 🎯 Learning Objectives

This project strengthened my understanding of:

* Python web application development
* Flask routing
* GET and POST requests
* HTML form handling
* Jinja2 templates
* SQLAlchemy ORM
* SQLite database integration
* CRUD operations
* Database queries
* Search and filtering
* Aggregate calculations
* Dynamic dashboard statistics
* Responsive Bootstrap design
* Flask project structure

---

## 🚀 Future Enhancements

Future versions could include:

* 👤 User authentication
* 📊 Interactive financial charts
* 📅 Monthly and yearly reports
* 💳 Multiple account management
* 🎯 Monthly budget limits
* 🔔 Budget notifications
* 📤 CSV/PDF export
* 📈 Spending trend analysis
* ☁️ Cloud database integration
* 📱 Progressive Web App support

---

## 📚 100 Days of Python

**Day 83 of 100 Days of Python 🐍**

This project represents another milestone in my Python development journey. It combines **Flask, SQLite, SQLAlchemy, CRUD operations, database queries, financial calculations, search/filtering, and responsive web development** into a practical application.

---

## 👩‍💻 Author

**Fatima Ch**

### ⭐ Project Status

**Completed — Day 83/100 ✅**

> Part of my ongoing **100 Days of Python** coding journey. 🐍💻
