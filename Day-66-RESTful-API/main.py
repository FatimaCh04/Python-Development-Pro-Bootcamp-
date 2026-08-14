from flask import Flask, jsonify, request
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

    def to_dict(self):

        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "rating": self.rating
        }


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()

    if Book.query.count() == 0:

        books = [

            Book(
                title="The Alchemist",
                author="Paulo Coelho",
                rating=8.5
            ),

            Book(
                title="Atomic Habits",
                author="James Clear",
                rating=9.2
            ),

            Book(
                title="The Psychology of Money",
                author="Morgan Housel",
                rating=9.0
            )

        ]

        db.session.add_all(books)
        db.session.commit()


# ==========================================
# GET ALL BOOKS
# ==========================================

@app.route("/books", methods=["GET"])
def get_books():

    books = Book.query.all()

    return jsonify(
        [book.to_dict() for book in books]
    )


# ==========================================
# GET SINGLE BOOK
# ==========================================

@app.route(
    "/books/<int:book_id>",
    methods=["GET"]
)
def get_book(book_id):

    book = db.get_or_404(
        Book,
        book_id
    )

    return jsonify(
        book.to_dict()
    )


# ==========================================
# ADD BOOK
# ==========================================

@app.route(
    "/books",
    methods=["POST"]
)
def add_book():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "JSON data is required"
        }), 400

    if not all(
        key in data
        for key in ["title", "author", "rating"]
    ):

        return jsonify({
            "error": "title, author and rating are required"
        }), 400

    new_book = Book(

        title=data["title"],

        author=data["author"],

        rating=float(data["rating"])

    )

    db.session.add(new_book)

    db.session.commit()

    return jsonify({
        "message": "Book added successfully",
        "book": new_book.to_dict()
    }), 201


# ==========================================
# UPDATE BOOK
# ==========================================

@app.route(
    "/books/<int:book_id>",
    methods=["PUT"]
)
def update_book(book_id):

    book = db.get_or_404(
        Book,
        book_id
    )

    data = request.get_json()

    if "title" in data:
        book.title = data["title"]

    if "author" in data:
        book.author = data["author"]

    if "rating" in data:
        book.rating = float(
            data["rating"]
        )

    db.session.commit()

    return jsonify({
        "message": "Book updated successfully",
        "book": book.to_dict()
    })


# ==========================================
# DELETE BOOK
# ==========================================

@app.route(
    "/books/<int:book_id>",
    methods=["DELETE"]
)
def delete_book(book_id):

    book = db.get_or_404(
        Book,
        book_id
    )

    db.session.delete(book)

    db.session.commit()

    return jsonify({
        "message": "Book deleted successfully"
    })


# ==========================================
# SEARCH BOOKS
# ==========================================

@app.route(
    "/search",
    methods=["GET"]
)
def search_books():

    title = request.args.get(
        "title",
        ""
    )

    books = Book.query.filter(
        Book.title.ilike(
            f"%{title}%"
        )
    ).all()

    return jsonify(
        [book.to_dict() for book in books]
    )


# ==========================================
# API HOME
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "message": "Welcome to the Books REST API",
        "endpoints": {
            "GET all books": "/books",
            "GET one book": "/books/<id>",
            "POST book": "/books",
            "PUT book": "/books/<id>",
            "DELETE book": "/books/<id>",
            "SEARCH": "/search?title=book"
        }
    })


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )