from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================================
# BOOK MODEL
# ==========================================

class Book(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    author = db.Column(
        db.String(150),
        nullable=False
    )

    rating = db.Column(
        db.Float,
        nullable=False
    )


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()

    # Add sample books only once

    if Book.query.count() == 0:

        sample_books = [

            Book(
                title="Harry Potter",
                author="J.K. Rowling",
                rating=9.0
            ),

            Book(
                title="The Alchemist",
                author="Paulo Coelho",
                rating=8.5
            ),

            Book(
                title="Atomic Habits",
                author="James Clear",
                rating=9.2
            )

        ]

        db.session.add_all(sample_books)

        db.session.commit()


# ==========================================
# HOME / BOOKSHELF
# ==========================================

@app.route("/")
def home():

    books = Book.query.order_by(
        Book.rating.desc()
    ).all()

    return render_template(
        "index.html",
        books=books
    )


# ==========================================
# ADD BOOK
# ==========================================

@app.route(
    "/add",
    methods=["GET", "POST"]
)
def add_book():

    if request.method == "POST":

        title = request.form["title"]

        author = request.form["author"]

        rating = float(
            request.form["rating"]
        )

        new_book = Book(
            title=title,
            author=author,
            rating=rating
        )

        db.session.add(new_book)

        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template(
        "add-book.html"
    )


# ==========================================
# EDIT BOOK
# ==========================================

@app.route(
    "/edit/<int:book_id>",
    methods=["GET", "POST"]
)
def edit_book(book_id):

    book = db.get_or_404(
        Book,
        book_id
    )

    if request.method == "POST":

        book.title = request.form["title"]

        book.author = request.form["author"]

        book.rating = float(
            request.form["rating"]
        )

        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template(
        "add-book.html",
        book=book
    )


# ==========================================
# DELETE BOOK
# ==========================================

@app.route(
    "/delete/<int:book_id>",
    methods=["POST"]
)
def delete_book(book_id):

    book = db.get_or_404(
        Book,
        book_id
    )

    db.session.delete(book)

    db.session.commit()

    return redirect(
        url_for("home")
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )