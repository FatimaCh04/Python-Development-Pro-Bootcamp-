# 📊 Sales Data Analyzer

> A Professional Python-based Sales Analytics & Machine Learning Project

<img width="1356" height="637" alt="OUTPUT 1" src="https://github.com/user-attachments/assets/f30674ad-6cc0-4f0f-a01f-0c7eeeda14a2" />

<img width="1356" height="640" alt="OUTPUT 2" src="https://github.com/user-attachments/assets/d595fe24-4230-4b89-af87-dc9028ac405a" />

## 📌 Project Overview

**Sales Data Analyzer** is a complete Data Analytics and Machine Learning application built using Python. It helps retail businesses analyze five years of sales data, clean datasets, generate visual reports, identify top-selling products, and predict future sales using Linear Regression.

The project automates the complete workflow from raw CSV files to professional PDF reports with insightful visualizations.

---

## ✨ Features

### 🧹 Data Cleaning
- Remove duplicate records
- Handle missing values
- Convert incorrect data types
- Validate dates
- Remove invalid sales values
- Export cleaned dataset

---

### 📈 Sales Analysis

Generate detailed reports including:

- Daily Sales
- Weekly Sales
- Monthly Sales
- Quarterly Sales
- Yearly Sales
- Product-wise Sales
- Category-wise Sales
- Region-wise Sales
- Revenue Analysis
- Profit Analysis
- Growth Percentage

---

### 📊 Data Visualization

Generate professional charts:

- 📈 Monthly Sales Trend
- 📊 Quarterly Sales Comparison
- 🥧 Region-wise Sales
- 📉 Product Sales
- 🔥 Correlation Heatmap
- 📦 Top Products Chart
- 📌 Histogram
- 📍 Scatter Plot
- 📉 Moving Average Trend

All charts are automatically saved in the **charts/** folder.

---

### 🏆 Business Insights

The application automatically finds:

- Top 5 Best Selling Products
- Top 10 Products
- Most Profitable Products
- Highest Revenue Category
- Best Performing Region
- Monthly Growth Rate
- Average Order Value

---

### 🤖 Machine Learning

Implemented using **Scikit-Learn Linear Regression**

The model predicts:

- Next Month Sales
- Future Revenue Trend

Evaluation Metrics

- R² Score
- MAE
- RMSE

---

### 📄 Professional PDF Report

Automatically generates a multi-page PDF report including:

- Executive Summary
- Dataset Overview
- Monthly Report
- Quarterly Report
- Top Products
- Business Insights
- Charts
- Prediction Results
- Recommendations

---

### 💻 Command Line Interface

Users can:

- Select custom date range
- Generate reports
- View analytics
- Predict sales
- Export results
- Save PDF report

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|----------|
| Python | Programming Language |
| Pandas | Data Processing |
| NumPy | Numerical Computing |
| Matplotlib | Charts |
| Seaborn | Data Visualization |
| Scikit-Learn | Machine Learning |
| ReportLab | PDF Generation |
| Argparse | CLI |
| Logging | Application Logs |

---

## 📂 Project Structure

```
Sales-Data-Analyzer/
│
├── charts/
│   ├── monthly_sales.png
│   ├── quarterly_sales.png
│   ├── heatmap.png
│   └── top_products.png
│
├── data/
│   └── sales_data.csv
│
├── reports/
│   ├── cleaned_data.csv
│   └── sales_report.pdf
│
├── src/
│   ├── data_cleaning.py
│   ├── analysis.py
│   ├── visualization.py
│   ├── prediction.py
│   ├── pdf_report.py
│   └── utils.py
│
├── logs/
│
├── tests/
│
├── requirements.txt
├── README.md
└── main.py
```

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/FatimaCh04/Python-Development-Pro-Bootcamp-/edit/main/Sales-Data-Analyzer.git
```

Move into project directory

```bash
cd Sales-Data-Analyzer
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the project

```bash
python main.py
```

---

## 📷 Sample Output

### Monthly Sales Trend

<img width="749" height="450" alt="newplot (3)" src="https://github.com/user-attachments/assets/4dd6503b-208a-4b13-9543-64945f3ae0d9" />


### Top Products

```
1️⃣ Laptop

2️⃣ Mobile

3️⃣ Tablet

4️⃣ Keyboard

5️⃣ Monitor
```

---

### Prediction

```
Next Month Sales

Rs. 532,420
```

---

## 📋 Sample Dataset

Columns

```
Date
Product
Category
Region
Units Sold
Unit Price
Sales
Profit
Discount
Customer
Payment Method
```

---

## 📦 Output Files

```
reports/

✔ cleaned_data.csv

✔ sales_report.pdf

charts/

✔ monthly_sales.png

✔ quarterly_sales.png

✔ heatmap.png

✔ top_products.png
```

---

## 📈 Future Improvements

- Interactive Streamlit Dashboard
- ARIMA Time-Series Forecasting
- Power BI Integration
- SQL Database Support
- Email Report Automation
- Web Application using Flask/Django

---

## 👨‍💻 Author

**Fatima Choudhry**

BS Computer Science Student

Python Developer | Data Analyst | Machine Learning Enthusiast

---

## ⭐ Support

If you found this project useful, don't forget to ⭐ the repository.

---
