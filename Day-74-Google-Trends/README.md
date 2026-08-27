# 🐍 Day 74 — Google Trends Data

## 📊 Resampling and Visualising Time Series

This project is part of **Angela Yu's 100 Days of Code: The Complete Python Pro Bootcamp**.

In Day 74, I worked with real-world time-series data from Google Trends and financial/economic datasets. The goal was to explore how search interest changes over time and compare it with real-world events and data.

## 🚀 What I Practiced

* Working with Pandas DataFrames
* Reading CSV datasets
* Cleaning and exploring data
* Converting strings into datetime objects
* Working with time-series data
* Resampling data
* Calculating rolling averages
* Comparing multiple datasets
* Using Matplotlib for data visualization
* Creating charts with two y-axes
* Formatting dates on charts

## 📈 Analysis Performed

### Tesla

Compared:

* Tesla Google Search Trends
* Tesla stock price

### Bitcoin

Compared:

* Bitcoin Google Search Trends
* Bitcoin price

Daily Bitcoin price data was resampled to monthly data to make it comparable with the Google Trends dataset.

### Unemployment

Compared:

* Google searches for "Unemployment Benefits"
* U.S. unemployment rate

The project also uses a **6-month rolling average** to make the long-term trend easier to understand and includes unemployment data through 2020.

## 📁 Project Files

```text
Day_74/
│
├── main.py
├── TESLA Search Trend vs Price.csv
├── Bitcoin Search Trend.csv
├── Daily Bitcoin Price.csv
├── UE Benefits Search vs UE Rate 2004-19.csv
└── UE Benefits Search vs UE Rate 2004-20.csv
```

## 🛠️ Technologies Used

* Python
* Pandas
* Matplotlib
* CSV
* Time-Series Data Analysis

## ▶️ How to Run

Install the required libraries:

```bash
pip install pandas matplotlib
```

Run the project:

```bash
python main.py
```

## 🎯 Key Learning

Day 74 helped me understand how to work with time-series datasets, resample data into comparable time periods, calculate rolling averages, and create meaningful visualizations from real-world data.

## 📚 Course

**100 Days of Code: The Complete Python Pro Bootcamp**


🐍 **Another day completed in my 100 Days of Code journey!**
