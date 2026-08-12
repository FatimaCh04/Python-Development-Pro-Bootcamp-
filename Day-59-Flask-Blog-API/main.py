from flask import Flask, render_template
import requests

app = Flask(__name__)


# ==========================================
# API URL
# ==========================================

API_URL = "https://jsonplaceholder.typicode.com/posts"


# ==========================================
# GET BLOG POSTS
# ==========================================

def get_posts():

    try:

        response = requests.get(
            API_URL,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:

        return []


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    posts = get_posts()

    return render_template(
        "index.html",
        posts=posts[:9]
    )


# ==========================================
# SINGLE POST
# ==========================================

@app.route("/post/<int:post_id>")
def show_post(post_id):

    posts = get_posts()

    selected_post = None

    for post in posts:

        if post["id"] == post_id:

            selected_post = post

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