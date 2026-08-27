# 🐍 100 Days of Python — Day 71

## Data Exploration with Pandas

This project practices the Day 71 learning goals from Angela Yu's
**100 Days of Code: The Complete Python Pro Bootcamp**.

The exercise focuses on loading a CSV dataset with Pandas and
exploring salary and unemployment information for different college
majors.

> **Dataset note:** `college_major_salaries.csv` in this repository is
> an original small practice dataset created for this implementation.
> It is designed to exercise the same Pandas techniques without
> reproducing the course's full dataset.

## What I Practiced

- Importing Pandas
- Reading CSV files
- Creating a DataFrame
- Inspecting rows with `head()` and `tail()`
- Checking columns
- Checking DataFrame shape
- Inspecting data types
- Using `describe()`
- Detecting missing values
- Sorting data
- Filtering rows
- Creating calculated columns
- Finding averages
- Exploring salary and unemployment data

## Project Files

```text
Day-71-Data-Exploration/
│
├── main.py
├── college_major_salaries.csv
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Main Pandas Concepts

### Load CSV

```python
df = pd.read_csv("college_major_salaries.csv")
```

### Inspect the data

```python
df.head()
df.tail()
df.columns
df.shape
df.dtypes
df.describe()
```

### Sort

```python
df.sort_values(
    by="Starting Median Salary",
    ascending=False
)
```

### Filter

```python
df[
    df["Mid-Career Median Salary"] >= 80000
]
```

### Create a new column

```python
df["Salary Increase"] = (
    df["Mid-Career Median Salary"]
    - df["Starting Median Salary"]
)
```

## Learning Goal

The goal of this day is not just to print a CSV. It is to become
comfortable using Pandas to inspect, clean, filter, sort, calculate,
and understand a real-world style dataset.

## Progress

**100 Days of Python — Day 71 ✅**
