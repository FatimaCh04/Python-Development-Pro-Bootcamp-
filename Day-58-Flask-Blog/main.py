from flask import Flask, render_template

app = Flask(__name__)


# ==========================================
# BLOG DATA
# ==========================================

posts = [
    {
        "id": 1,
        "title": "My Python Learning Journey",
        "subtitle": "How I started learning Python",
        "body": (
            "Python has become an important part of my "
            "programming journey. I started with basic "
            "syntax and gradually moved toward projects "
            "and web development."
        ),
        "author": "Fatima",
        "date": "Day 58"
    },
    {
        "id": 2,
        "title": "Learning Flask",
        "subtitle": "Building websites with Python",
        "body": (
            "Flask makes it possible to build web "
            "applications using Python. Routes, templates "
            "and Jinja make it easy to create dynamic pages."
        ),
        "author": "Fatima",
        "date": "Day 58"
    },
    {
        "id": 3,
        "title": "Why Consistency Matters",
        "subtitle": "My 100 Days of Python journey",
        "body": (
            "Practicing every day has helped me understand "
            "programming concepts better. Small projects "
            "make learning more interesting and practical."
        ),
        "author": "Fatima",
        "date": "Day 58"
    }
]


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        posts=posts
    )


# ==========================================
# SINGLE POST
# ==========================================

@app.route("/post/<int:post_id>")
def post(post_id):

    selected_post = None

    for item in posts:

        if item["id"] == post_id:

            selected_post = item

            break

    if selected_post is None:

        return render_template(
            "post.html",
            post=None
        ), 404

    return render_template(
        "post.html",
        post=selected_post
    )


# ==========================================
# ABOUT
# ==========================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ==========================================
# CONTACT
# ==========================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )