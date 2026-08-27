from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================
# Database Model
# =========================

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)


# Create database
with app.app_context():
    db.create_all()


# =========================
# Dashboard
# =========================

@app.route("/")
def index():

    search = request.args.get("search", "")
    category_filter = request.args.get("category", "")
    type_filter = request.args.get("type", "")

    query = Transaction.query

    # Search
    if search:
        query = query.filter(
            db.or_(
                Transaction.title.ilike(f"%{search}%"),
                Transaction.category.ilike(f"%{search}%")
            )
        )

    # Category filter
    if category_filter:
        query = query.filter(
            Transaction.category == category_filter
        )

    # Income / Expense filter
    if type_filter:
        query = query.filter(
            Transaction.transaction_type == type_filter
        )

    transactions = query.order_by(
        Transaction.id.desc()
    ).all()

    # Total income
    income_result = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_type == "Income"
    ).scalar()

    total_income = income_result or 0

    # Total expenses
    expense_result = db.session.query(
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_type == "Expense"
    ).scalar()

    total_expenses = expense_result or 0

    # Balance
    balance = total_income - total_expenses

    # Number of transactions
    total_transactions = Transaction.query.count()

    # Categories
    categories = db.session.query(
        Transaction.category
    ).distinct().order_by(
        Transaction.category
    ).all()

    categories = [category[0] for category in categories]

    # Expense category summary
    expense_categories = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.transaction_type == "Expense"
    ).group_by(
        Transaction.category
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()

    return render_template(
        "index.html",
        transactions=transactions,
        categories=categories,
        expense_categories=expense_categories,
        search=search,
        category_filter=category_filter,
        type_filter=type_filter,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        total_transactions=total_transactions
    )


# =========================
# Add Transaction
# =========================

@app.route("/add", methods=["GET", "POST"])
def add_transaction():

    if request.method == "POST":

        title = request.form["title"]
        amount = float(request.form["amount"])
        transaction_type = request.form["transaction_type"]
        category = request.form["category"]
        date = request.form["date"]
        notes = request.form["notes"]

        transaction = Transaction(
            title=title,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            date=date,
            notes=notes
        )

        db.session.add(transaction)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("add.html")


# =========================
# Edit Transaction
# =========================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_transaction(id):

    transaction = Transaction.query.get_or_404(id)

    if request.method == "POST":

        transaction.title = request.form["title"]
        transaction.amount = float(request.form["amount"])
        transaction.transaction_type = request.form["transaction_type"]
        transaction.category = request.form["category"]
        transaction.date = request.form["date"]
        transaction.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        transaction=transaction
    )


# =========================
# Delete Transaction
# =========================

@app.route("/delete/<int:id>")
def delete_transaction(id):

    transaction = Transaction.query.get_or_404(id)

    db.session.delete(transaction)
    db.session.commit()

    return redirect(url_for("index"))


# =========================
# Run Application
# =========================

if __name__ == "__main__":
    app.run(debug=True)