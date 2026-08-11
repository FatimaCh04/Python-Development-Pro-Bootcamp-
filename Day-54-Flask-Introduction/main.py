from flask import Flask, render_template


# ==========================================
# CREATE FLASK APPLICATION
# ==========================================

app = Flask(__name__)


# ==========================================
# HOME ROUTE
# ==========================================

@app.route("/")
def home():
    return render_template(
        "index.html",
        name="Python Developer",
        day=54
    )


# ==========================================
# ABOUT ROUTE
# ==========================================

@app.route("/about")
def about():
    return """
    <h1>About This Project</h1>
    <p>
        This is my Day 54 Flask project
        from Angela Yu's 100 Days of Python.
    </p>
    """


# ==========================================
# DYNAMIC ROUTE
# ==========================================

@app.route("/hello/<username>")
def hello(username):

    return f"""
    <h1>Hello {username}! 👋</h1>
    <p>Welcome to my Flask application.</p>
    """


# ==========================================
# PROJECT ROUTE
# ==========================================

@app.route("/project")
def project():

    return """
    <h1>Day 54 Flask Project 🚀</h1>

    <p>
        I am learning Python web development
        with Flask.
    </p>

    <ul>
        <li>Flask</li>
        <li>Routes</li>
        <li>Decorators</li>
        <li>Templates</li>
        <li>Dynamic URLs</li>
    </ul>
    """


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )