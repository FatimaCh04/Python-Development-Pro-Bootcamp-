from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    expenses = Expense.query.order_by(Expense.id.desc()).all()

    total = sum(expense.amount for expense in expenses)

    return render_template(
        "index.html",
        expenses=expenses,
        total=total
    )


@app.route("/add", methods=["GET", "POST"])
def add_expense():

    if request.method == "POST":
        title = request.form["title"]
        amount = float(request.form["amount"])
        category = request.form["category"]
        date = request.form["date"]

        new_expense = Expense(
            title=title,
            amount=amount,
            category=category,
            date=date
        )

        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("add.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):

    expense = Expense.query.get_or_404(id)

    if request.method == "POST":
        expense.title = request.form["title"]
        expense.amount = float(request.form["amount"])
        expense.category = request.form["category"]
        expense.date = request.form["date"]

        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit.html", expense=expense)


@app.route("/delete/<int:id>")
def delete_expense(id):

    expense = Expense.query.get_or_404(id)

    db.session.delete(expense)
    db.session.commit()

    return redirect(url_for("home"))


@app.route("/clear")
def clear_expenses():

    Expense.query.delete()
    db.session.commit()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)