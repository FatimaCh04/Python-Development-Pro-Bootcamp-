# 📊 Day 85 — Expense Analytics Dashboard

A professional **Expense Analytics Dashboard** built with **Python, Flask, Pandas, and Matplotlib**. The application analyzes financial transaction data from a CSV file and transforms it into meaningful statistics, summaries, and visual insights.

This project focuses on practical **data analysis, visualization, filtering, and Flask dashboard development**.

---

## 🚀 Project Overview

Managing financial data becomes much easier when raw transaction records can be transformed into clear visual insights.

The **Expense Analytics Dashboard** reads transaction data from a CSV file, processes it using **Pandas**, performs financial calculations, and generates charts using **Matplotlib**.

Users can view:

* Total income
* Total expenses
* Current balance
* Number of transactions
* Expenses by category
* Monthly expense trends
* Detailed transaction records

The dashboard also provides filtering options and allows users to download the original CSV dataset.

---

## ✨ Features

* 📂 CSV-based transaction management
* 📊 Interactive financial dashboard
* 💰 Total income calculation
* 💸 Total expense calculation
* 💵 Automatic balance calculation
* 📈 Monthly expense visualization
* 🏷️ Category-wise expense analysis
* 🔎 Transaction filtering
* 📋 Detailed transaction table
* 📥 CSV download functionality
* 📉 Matplotlib-generated charts
* 📱 Responsive Bootstrap interface
* ⚡ Automatic sample dataset generation

---

## 🛠️ Technologies Used

| Technology      | Purpose                      |
| --------------- | ---------------------------- |
| **Python**      | Core programming language    |
| **Flask**       | Web application framework    |
| **Pandas**      | Data processing and analysis |
| **Matplotlib**  | Data visualization           |
| **HTML5**       | Web page structure           |
| **CSS3**        | Custom styling               |
| **Bootstrap 5** | Responsive UI                |
| **Jinja2**      | Dynamic template rendering   |
| **CSV**         | Transaction data storage     |

---

## 🏗️ Application Architecture

```text
                 CSV Dataset
                      │
                      ▼
                   Pandas
                      │
             Data Processing
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
   Financial Analysis        Data Visualization
          │                       │
          │                   Matplotlib
          │                       │
          └───────────┬───────────┘
                      ▼
                 Flask App
                      │
                      ▼
              Web Dashboard
```

---

## 📁 Project Structure

```text
Day85-Expense-Analytics/
│
├── app.py
├── requirements.txt
│
├── data/
│   └── transactions.csv
│
├── static/
│   ├── css/
│   │   └── styles.css
│   │
│   └── charts/
│       ├── category_expenses.png
│       └── monthly_expenses.png
│
└── templates/
    ├── base.html
    └── index.html
```

---

## 📊 Dashboard Metrics

The application calculates the following metrics dynamically.

### Total Income

The sum of all transactions classified as **Income**.

### Total Expenses

The sum of all transactions classified as **Expense**.

### Balance

```text
Balance = Total Income - Total Expenses
```

### Total Transactions

The total number of transaction records currently displayed.

---

## 📈 Data Visualization

### Expenses by Category

The dashboard groups expense transactions by category and generates a bar chart using Matplotlib.

Example categories include:

```text
Food
Transport
Shopping
Bills
Entertainment
```

### Monthly Expenses

Expense data is grouped by month to visualize spending trends over time.

This makes it easier to identify periods with higher or lower spending.

---

## 🔎 Filtering

Users can filter the transaction data using:

### Category

```text
All Categories
Food
Transport
Shopping
Bills
Entertainment
```

### Transaction Type

```text
All Types
Income
Expense
```

The dashboard updates the displayed dataset and calculations based on the selected filters.

---

## 📥 CSV Download

The application includes a **Download CSV** feature that allows users to download the transaction dataset directly from the dashboard.

---

## 📄 Dataset Format

The CSV file uses the following structure:

```csv
Date,Description,Category,Type,Amount
2026-01-05,Monthly Salary,Salary,Income,5000
2026-01-10,Groceries,Food,Expense,250
2026-01-15,Transport,Transport,Expense,100
```

### Columns

| Column        | Description             |
| ------------- | ----------------------- |
| `Date`        | Transaction date        |
| `Description` | Transaction description |
| `Category`    | Transaction category    |
| `Type`        | Income or Expense       |
| `Amount`      | Transaction amount      |

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
```

### 2. Navigate to the Project

```bash
cd Day85-Expense-Analytics
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Environment

**Windows:**

```bash
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
python app.py
```

Then open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 📦 Dependencies

The project requires:

```text
Flask
Pandas
Matplotlib
```

Install them using:

```bash
pip install -r requirements.txt
```

---

## 🧠 Key Concepts Practiced

This project helped strengthen my understanding of:

* Python data analysis
* Pandas DataFrames
* CSV file handling
* Data filtering
* Data grouping
* Aggregation
* Financial calculations
* Matplotlib visualization
* Flask routing
* Jinja2 templates
* Dynamic HTML rendering
* Query parameters
* File downloads
* Responsive web design
* Dashboard development

---

## 🎯 Learning Outcomes

By completing this project, I practiced converting raw financial data into useful information through a complete workflow:

```text
Raw Data
   ↓
Data Cleaning
   ↓
Data Analysis
   ↓
Calculations
   ↓
Visualization
   ↓
Flask Dashboard
```

This demonstrates how Python can be used not only for programming but also for **real-world data analysis and decision-making**.

---

## 🔮 Future Improvements

Possible future enhancements include:

* 👤 User authentication
* 💾 Database integration
* 📅 Custom date-range filtering
* 📊 Interactive charts
* 📈 Income vs Expense comparison
* 💳 Budget management
* 🔔 Budget alerts
* 📤 Excel and PDF export
* 📱 Progressive Web App support
* ☁️ Cloud deployment

---

## 🐍 100 Days of Python

**Day 85 / 100 — Completed ✅**

This project represents another milestone in my **100 Days of Python** journey.

The focus of this project was on combining **Python, Pandas, Matplotlib, and Flask** to build a practical data analytics dashboard.

---

## 👩‍💻 Author

**Fatima Ch**

---

## ⭐ Project Status

**Completed — Day 85/100 🚀**

Continuing the journey of learning, building, and improving one Python project at a time. 🐍💻

---

⭐ If you find this project useful, consider giving the repository a star!
