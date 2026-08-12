from flask import Flask, render_template

app = Flask(__name__)


# ==========================================
# HOME ROUTE
# ==========================================

@app.route("/")
def home():

    user = {
        "name": "Fatima",
        "profession": "Python Developer",
        "description": (
            "I am learning Python, Flask "
            "and web development."
        )
    }

    skills = [
        "Python",
        "Flask",
        "HTML",
        "CSS",
        "Git & GitHub"
    ]

    projects = [
        "Higher or Lower Game",
        "Automated Data Entry",
        "Flask Web Application"
    ]

    return render_template(
        "index.html",
        user=user,
        skills=skills,
        projects=projects
    )


# ==========================================
# ABOUT ROUTE
# ==========================================

@app.route("/about")
def about():

    return """
    <h1>About Me</h1>
    <p>
        I am learning Flask and Jinja
        as part of my 100 Days of Python journey.
    </p>
    """


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)