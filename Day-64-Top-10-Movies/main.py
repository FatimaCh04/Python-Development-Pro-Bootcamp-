from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# ==========================================
# DATABASE
# ==========================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================================
# MOVIE MODEL
# ==========================================

class Movie(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    year = db.Column(
        db.Integer,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    rating = db.Column(
        db.Float,
        nullable=False
    )

    review = db.Column(
        db.Text,
        nullable=False
    )

    img_url = db.Column(
        db.String(500),
        nullable=False
    )


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()

    if Movie.query.count() == 0:

        movies = [

            Movie(
                title="The Shawshank Redemption",
                year=1994,
                description="Two imprisoned men bond over many years.",
                rating=9.3,
                review="An unforgettable classic.",
                img_url="https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg"
            ),

            Movie(
                title="The Dark Knight",
                year=2008,
                description="Batman faces a criminal mastermind known as the Joker.",
                rating=9.0,
                review="Brilliant storytelling and performances.",
                img_url="https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg"
            ),

            Movie(
                title="Inception",
                year=2010,
                description="A skilled thief enters people's dreams.",
                rating=8.8,
                review="Mind-bending and visually stunning.",
                img_url="https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg"
            )

        ]

        db.session.add_all(movies)
        db.session.commit()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    movies = Movie.query.order_by(
        Movie.rating.desc()
    ).all()

    return render_template(
        "index.html",
        movies=movies
    )


# ==========================================
# ADD MOVIE
# ==========================================

@app.route(
    "/add",
    methods=["GET", "POST"]
)
def add_movie():

    if request.method == "POST":

        title = request.form["title"]
        year = int(request.form["year"])
        description = request.form["description"]
        rating = float(request.form["rating"])
        review = request.form["review"]
        img_url = request.form["img_url"]

        movie = Movie(
            title=title,
            year=year,
            description=description,
            rating=rating,
            review=review,
            img_url=img_url
        )

        db.session.add(movie)
        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template(
        "add.html"
    )


# ==========================================
# EDIT MOVIE
# ==========================================

@app.route(
    "/edit/<int:movie_id>",
    methods=["GET", "POST"]
)
def edit_movie(movie_id):

    movie = db.get_or_404(
        Movie,
        movie_id
    )

    if request.method == "POST":

        movie.rating = float(
            request.form["rating"]
        )

        movie.review = request.form["review"]

        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template(
        "edit.html",
        movie=movie
    )


# ==========================================
# DELETE MOVIE
# ==========================================

@app.route(
    "/delete/<int:movie_id>",
    methods=["POST"]
)
def delete_movie(movie_id):

    movie = db.get_or_404(
        Movie,
        movie_id
    )

    db.session.delete(movie)
    db.session.commit()

    return redirect(
        url_for("home")
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)