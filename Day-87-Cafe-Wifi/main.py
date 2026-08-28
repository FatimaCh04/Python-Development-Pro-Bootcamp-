from flask import Flask, render_template, request, redirect, url_for
import csv
import os


app = Flask(__name__)

CSV_FILE = "cafe-data.csv"


# ============================================================
# Helper Functions
# ============================================================

def read_cafes():
    """Read all cafes from the CSV file."""

    if not os.path.exists(CSV_FILE):
        return []

    with open(
        CSV_FILE,
        mode="r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


def add_cafe(cafe_data):
    """Add a new cafe to the CSV file."""

    file_exists = os.path.exists(CSV_FILE)

    fieldnames = [
        "Cafe Name",
        "Location",
        "Open",
        "Close",
        "Coffee",
        "Wifi",
        "Power",
        "Seats",
        "Price",
        "Map URL"
    ]

    with open(
        CSV_FILE,
        mode="a",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(cafe_data)


# ============================================================
# Home Page
# ============================================================

@app.route("/")
def home():

    cafes = read_cafes()

    return render_template(
        "index.html",
        cafes=cafes
    )


# ============================================================
# Cafes Page
# ============================================================

@app.route("/cafes")
def cafes():

    all_cafes = read_cafes()

    return render_template(
        "cafes.html",
        cafes=all_cafes
    )


# ============================================================
# Add Cafe
# ============================================================

@app.route(
    "/add",
    methods=["GET", "POST"]
)
def add():

    if request.method == "POST":

        cafe_data = {
            "Cafe Name": request.form.get(
                "cafe_name"
            ),

            "Location": request.form.get(
                "location"
            ),

            "Open": request.form.get(
                "open"
            ),

            "Close": request.form.get(
                "close"
            ),

            "Coffee": request.form.get(
                "coffee"
            ),

            "Wifi": request.form.get(
                "wifi"
            ),

            "Power": request.form.get(
                "power"
            ),

            "Seats": request.form.get(
                "seats"
            ),

            "Price": request.form.get(
                "price"
            ),

            "Map URL": request.form.get(
                "map_url"
            )
        }

        add_cafe(cafe_data)

        return redirect(
            url_for("cafes")
        )

    return render_template("add.html")


# ============================================================
# Delete Cafe
# ============================================================

@app.route(
    "/delete/<int:cafe_index>",
    methods=["POST"]
)
def delete_cafe(cafe_index):

    cafes = read_cafes()

    if 0 <= cafe_index < len(cafes):

        cafes.pop(cafe_index)

        fieldnames = [
            "Cafe Name",
            "Location",
            "Open",
            "Close",
            "Coffee",
            "Wifi",
            "Power",
            "Seats",
            "Price",
            "Map URL"
        ]

        with open(
            CSV_FILE,
            mode="w",
            encoding="utf-8",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            writer.writeheader()

            writer.writerows(cafes)

    return redirect(
        url_for("cafes")
    )


# ============================================================
# Run Application
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )