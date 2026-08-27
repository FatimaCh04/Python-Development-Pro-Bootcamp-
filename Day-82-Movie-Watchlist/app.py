from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Movie Model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Unwatched")
    notes = db.Column(db.Text, nullable=True)


# Create database
with app.app_context():
    db.create_all()


# Home / Watchlist
@app.route("/")
def index():

    search = request.args.get("search", "")
    genre_filter = request.args.get("genre", "")
    status_filter = request.args.get("status", "")

    query = Movie.query

    # Search by title or genre
    if search:
        query = query.filter(
            db.or_(
                Movie.title.ilike(f"%{search}%"),
                Movie.genre.ilike(f"%{search}%")
            )
        )

    # Genre filter
    if genre_filter:
        query = query.filter(
            Movie.genre == genre_filter
        )

    # Status filter
    if status_filter:
        query = query.filter(
            Movie.status == status_filter
        )

    movies = query.order_by(
        Movie.id.desc()
    ).all()

    # Statistics
    total = Movie.query.count()

    watched = Movie.query.filter_by(
        status="Watched"
    ).count()

    unwatched = Movie.query.filter_by(
        status="Unwatched"
    ).count()

    average_rating = db.session.query(
        db.func.avg(Movie.rating)
    ).scalar()

    if average_rating is None:
        average_rating = 0

    # Get unique genres
    genres = db.session.query(
        Movie.genre
    ).distinct().order_by(
        Movie.genre
    ).all()

    genres = [genre[0] for genre in genres]

    return render_template(
        "index.html",
        movies=movies,
        genres=genres,
        search=search,
        genre_filter=genre_filter,
        status_filter=status_filter,
        total=total,
        watched=watched,
        unwatched=unwatched,
        average_rating=round(average_rating, 1)
    )


# Add Movie
@app.route("/add", methods=["GET", "POST"])
def add_movie():

    if request.method == "POST":

        title = request.form["title"]
        genre = request.form["genre"]
        year = int(request.form["year"])
        rating = float(request.form["rating"])
        notes = request.form["notes"]

        new_movie = Movie(
            title=title,
            genre=genre,
            year=year,
            rating=rating,
            status="Unwatched",
            notes=notes
        )

        db.session.add(new_movie)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("add.html")


# Edit Movie
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_movie(id):

    movie = Movie.query.get_or_404(id)

    if request.method == "POST":

        movie.title = request.form["title"]
        movie.genre = request.form["genre"]
        movie.year = int(request.form["year"])
        movie.rating = float(request.form["rating"])
        movie.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        movie=movie
    )


# Delete Movie
@app.route("/delete/<int:id>")
def delete_movie(id):

    movie = Movie.query.get_or_404(id)

    db.session.delete(movie)
    db.session.commit()

    return redirect(url_for("index"))


# Mark Movie Watched / Unwatched
@app.route("/toggle/<int:id>")
def toggle_status(id):

    movie = Movie.query.get_or_404(id)

    if movie.status == "Watched":
        movie.status = "Unwatched"
    else:
        movie.status = "Watched"

    db.session.commit()

    return redirect(url_for("index"))


# Clear Watched Movies
@app.route("/clear-watched")
def clear_watched():

    Movie.query.filter_by(
        status="Watched"
    ).delete()

    db.session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)