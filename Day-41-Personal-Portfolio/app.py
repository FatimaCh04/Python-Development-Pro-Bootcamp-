from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def home():
    skills = [
        "Python",
        "HTML",
        "CSS",
        "Flask",
        "GitHub"
    ]

    projects = [
        {
            "name": "Python Calculator",
            "description": "A beginner-friendly calculator built with Python."
        },
        {
            "name": "Weather App",
            "description": "A simple application that works with weather data."
        },
        {
            "name": "Expense Tracker",
            "description": "A small project for recording daily expenses."
        }
    ]

    return render_template(
        "index.html",
        skills=skills,
        projects=projects
    )


@app.route("/about")
def about():
    return """
    <h1>About Me</h1>
    <p>
        I am learning Python and web development
        through hands-on projects.
    </p>
    """


if __name__ == "__main__":
    app.run(debug=True)