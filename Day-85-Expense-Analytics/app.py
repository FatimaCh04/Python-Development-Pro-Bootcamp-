import os
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from flask import Flask, render_template, request, send_file


app = Flask(__name__)


# =========================
# Configuration
# =========================

DATA_FILE = "data/transactions.csv"
CHART_FOLDER = "static/charts"

os.makedirs("data", exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)


# =========================
# Create Sample Dataset
# =========================

def create_sample_data():

    if not os.path.exists(DATA_FILE):

        data = {
            "Date": [
                "2026-01-05",
                "2026-01-10",
                "2026-01-15",
                "2026-02-03",
                "2026-02-12",
                "2026-02-20",
                "2026-03-02",
                "2026-03-11",
                "2026-03-25",
                "2026-04-05",
                "2026-04-18",
                "2026-05-01"
            ],

            "Description": [
                "Monthly Salary",
                "Groceries",
                "Transport",
                "Freelance Work",
                "Shopping",
                "Restaurant",
                "Monthly Salary",
                "Electricity Bill",
                "Groceries",
                "Freelance Work",
                "Entertainment",
                "Monthly Salary"
            ],

            "Category": [
                "Salary",
                "Food",
                "Transport",
                "Freelance",
                "Shopping",
                "Food",
                "Salary",
                "Bills",
                "Food",
                "Freelance",
                "Entertainment",
                "Salary"
            ],

            "Type": [
                "Income",
                "Expense",
                "Expense",
                "Income",
                "Expense",
                "Expense",
                "Income",
                "Expense",
                "Expense",
                "Income",
                "Expense",
                "Income"
            ],

            "Amount": [
                5000,
                250,
                100,
                1200,
                350,
                180,
                5000,
                200,
                300,
                1500,
                250,
                5000
            ]
        }

        df = pd.DataFrame(data)

        df.to_csv(DATA_FILE, index=False)


# Create dataset when application starts
create_sample_data()


# =========================
# Load Data
# =========================

def load_data():

    df = pd.read_csv(DATA_FILE)

    df["Date"] = pd.to_datetime(df["Date"])

    return df


# =========================
# Generate Category Chart
# =========================

def create_category_chart(df):

    expenses = df[df["Type"] == "Expense"]

    category_data = expenses.groupby(
        "Category"
    )["Amount"].sum()

    if category_data.empty:
        return

    plt.figure(figsize=(8, 5))

    category_data.plot(
        kind="bar"
    )

    plt.title("Expenses by Category")

    plt.xlabel("Category")

    plt.ylabel("Amount")

    plt.xticks(rotation=45)

    plt.tight_layout()

    chart_path = os.path.join(
        CHART_FOLDER,
        "category_expenses.png"
    )

    plt.savefig(chart_path)

    plt.close()


# =========================
# Generate Monthly Chart
# =========================

def create_monthly_chart(df):

    expenses = df[df["Type"] == "Expense"].copy()

    if expenses.empty:
        return

    expenses["Month"] = expenses["Date"].dt.strftime(
        "%Y-%m"
    )

    monthly_data = expenses.groupby(
        "Month"
    )["Amount"].sum()

    plt.figure(figsize=(9, 5))

    monthly_data.plot(
        kind="line",
        marker="o"
    )

    plt.title("Monthly Expenses")

    plt.xlabel("Month")

    plt.ylabel("Amount")

    plt.xticks(rotation=45)

    plt.grid(True)

    plt.tight_layout()

    chart_path = os.path.join(
        CHART_FOLDER,
        "monthly_expenses.png"
    )

    plt.savefig(chart_path)

    plt.close()


# =========================
# Dashboard
# =========================

@app.route("/")
def index():

    df = load_data()

    category_filter = request.args.get(
        "category",
        ""
    )

    type_filter = request.args.get(
        "type",
        ""
    )

    # Apply category filter
    if category_filter:

        df = df[
            df["Category"] == category_filter
        ]


    # Apply type filter
    if type_filter:

        df = df[
            df["Type"] == type_filter
        ]


    # Calculate statistics
    total_income = df[
        df["Type"] == "Income"
    ]["Amount"].sum()


    total_expenses = df[
        df["Type"] == "Expense"
    ]["Amount"].sum()


    balance = total_income - total_expenses


    total_transactions = len(df)


    # Create charts
    create_category_chart(df)

    create_monthly_chart(df)


    # Expense category summary
    expense_summary = (
        df[df["Type"] == "Expense"]
        .groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )


    categories = sorted(
        df["Category"].unique()
    )


    transactions = df.copy()

    transactions["Date"] = transactions[
        "Date"
    ].dt.strftime("%Y-%m-%d")


    return render_template(
        "index.html",
        transactions=transactions.to_dict(
            orient="records"
        ),
        categories=categories,
        expense_summary=expense_summary.to_dict(),
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        total_transactions=total_transactions,
        category_filter=category_filter,
        type_filter=type_filter
    )


# =========================
# Download CSV
# =========================

@app.route("/download")
def download():

    return send_file(
        DATA_FILE,
        as_attachment=True,
        download_name="transactions.csv"
    )


# =========================
# Run Application
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )