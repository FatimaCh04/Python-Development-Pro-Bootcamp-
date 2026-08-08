import json
import os
from datetime import datetime


FILE_NAME = "expenses.json"


def load_expenses():
    """Load expenses from JSON file."""

    if not os.path.exists(FILE_NAME):
        return []

    try:
        with open(FILE_NAME, "r") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def save_expenses(expenses):
    """Save expenses to JSON file."""

    with open(FILE_NAME, "w") as file:
        json.dump(expenses, file, indent=4)


def add_expense():
    """Add a new expense."""

    print("\n--- Add New Expense ---")

    category = input("Category: ").strip()
    amount = input("Amount: ").strip()
    note = input("Note: ").strip()

    if not category or not amount:
        print("❌ Category and amount are required.")
        return

    try:
        amount = float(amount)

        if amount <= 0:
            print("❌ Amount must be greater than 0.")
            return

    except ValueError:
        print("❌ Amount must be a number.")
        return

    expense = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "amount": amount,
        "note": note
    }

    expenses = load_expenses()
    expenses.append(expense)

    save_expenses(expenses)

    print("\n✅ Expense added successfully!")


def show_expenses():
    """Display all saved expenses."""

    expenses = load_expenses()

    print("\n--- 💰 Expense Records ---")

    if not expenses:
        print("No expenses found.")
        return

    total = 0

    for number, expense in enumerate(expenses, start=1):

        print(f"\n#{number}")
        print(f"Date     : {expense['date']}")
        print(f"Category : {expense['category']}")
        print(f"Amount   : ${expense['amount']:.2f}")
        print(f"Note     : {expense['note']}")

        total += expense["amount"]

    print("\n" + "-" * 35)
    print(f"Total    : ${total:.2f}")


def main():

    print("=" * 45)
    print("        💰 EXPENSE TRACKER")
    print("=" * 45)

    while True:

        print("\n1. Add Expense")
        print("2. View Expenses")
        print("3. Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            add_expense()

        elif choice == "2":
            show_expenses()

        elif choice == "3":
            print("\n👋 Goodbye!")
            break

        else:
            print("❌ Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()