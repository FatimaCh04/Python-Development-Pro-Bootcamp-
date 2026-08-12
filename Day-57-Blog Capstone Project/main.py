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
            "Python is one of the most powerful and "
            "beginner-friendly programming languages. "
            "I started my journey by learning variables, "
            "loops, functions and object-oriented programming."
        ),
        "author": "Fatima"
    },
    {
        "id": 2,
        "title": "Why I Started Flask",
        "subtitle": "Building websites with Python",
        "body": (
            "Flask allows Python developers to build "
            "web applications. It provides routing, "
            "templates and many useful features for "
            "creating dynamic websites."
        ),
        "author": "Fatima"
    },
    {
        "id": 3,
        "title": "My 100 Days of Python Challenge",
        "subtitle": "Learning something new every day",
        "body": (
            "The 100 Days of Python challenge has helped "
            "me practice Python consistently. Every day "
            "I build a small project and learn new concepts."
        ),
        "author": "Fatima"
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
# BLOG POST
# ==========================================

@app.route("/post/<int:post_id>")
def show_post(post_id):

    selected_post = None

    for post in posts:

        if post["id"] == post_id:

            selected_post = post

            break

    if selected_post is None:

        return "Post not found", 404

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
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )