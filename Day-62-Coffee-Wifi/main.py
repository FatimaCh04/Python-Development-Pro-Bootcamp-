from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# ==============================
# DATABASE CONFIG
# ==============================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==============================
# CAFE MODEL
# ==============================

class Cafe(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(200),
        nullable=False
    )

    coffee_price = db.Column(
        db.String(50),
        nullable=False
    )

    wifi = db.Column(
        db.Boolean,
        default=False
    )

    power = db.Column(
        db.Boolean,
        default=False
    )

    coffee = db.Column(
        db.Boolean,
        default=False
    )


# ==============================
# CREATE DATABASE
# ==============================

with app.app_context():

    db.create_all()

    if Cafe.query.count() == 0:

        cafes = [

            Cafe(
                name="Coffee Corner",
                location="Downtown",
                coffee_price="$3",
                wifi=True,
                power=True,
                coffee=True
            ),

            Cafe(
                name="The Study Cafe",
                location="Main Street",
                coffee_price="$4",
                wifi=True,
                power=True,
                coffee=True
            ),

            Cafe(
                name="Morning Brew",
                location="City Center",
                coffee_price="$2.5",
                wifi=True,
                power=False,
                coffee=True
            )

        ]

        db.session.add_all(cafes)
        db.session.commit()


# ==============================
# HOME
# ==============================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==============================
# ALL CAFES
# ==============================

@app.route("/cafes")
def cafes():

    all_cafes = Cafe.query.all()

    return render_template(
        "cafes.html",
        cafes=all_cafes
    )


# ==============================
# ADD CAFE
# ==============================

@app.route(
    "/add-cafe",
    methods=["GET", "POST"]
)
def add_cafe():

    if request.method == "POST":

        name = request.form["name"]
        location = request.form["location"]
        coffee_price = request.form["coffee_price"]

        wifi = "wifi" in request.form
        power = "power" in request.form
        coffee = "coffee" in request.form

        new_cafe = Cafe(
            name=name,
            location=location,
            coffee_price=coffee_price,
            wifi=wifi,
            power=power,
            coffee=coffee
        )

        db.session.add(new_cafe)
        db.session.commit()

        return redirect(
            url_for("cafes")
        )

    return render_template(
        "add-cafe.html"
    )


# ==============================
# DELETE CAFE
# ==============================

@app.route(
    "/delete/<int:cafe_id>",
    methods=["POST"]
)
def delete_cafe(cafe_id):

    cafe = db.get_or_404(
        Cafe,
        cafe_id
    )

    db.session.delete(cafe)
    db.session.commit()

    return redirect(
        url_for("cafes")
    )


# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":

    app.run(
        debug=True
    )