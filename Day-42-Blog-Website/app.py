from flask import Flask, render_template, abort


app = Flask(__name__)


posts = [
    {
        "id": 1,
        "title": "My Python Learning Journey",
        "subtitle": "How I started learning Python",
        "author": "Python Learner",
        "date": "August 2026",
        "content": (
            "Python is one of the most beginner-friendly programming "
            "languages. I started learning it to improve my programming "
            "and problem-solving skills."
        ),
    },
    {
        "id": 2,
        "title": "Learning Flask",
        "subtitle": "Building websites with Python",
        "author": "Python Learner",
        "date": "August 2026",
        "content": (
            "Flask makes it possible to build web applications with "
            "Python. I learned how routes, templates and static files "
            "work together to create a website."
        ),
    },
    {
        "id": 3,
        "title": "Consistency Matters",
        "subtitle": "One day at a time",
        "author": "Python Learner",
        "date": "August 2026",
        "content": (
            "Learning programming takes time and consistency. Building "
            "small projects every day helps me understand concepts "
            "better and keeps me motivated."
        ),
    },
]


@app.route("/")
def home():
    return render_template(
        "index.html",
        posts=posts
    )


@app.route("/post/<int:post_id>")
def post(post_id):

    selected_post = next(
        (
            item
            for item in posts
            if item["id"] == post_id
        ),
        None
    )

    if selected_post is None:
        abort(404)

    return render_template(
        "post.html",
        post=selected_post
    )


@app.errorhandler(404)
def not_found(error):
    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    <a href="/">Return Home</a>
    """, 404


if __name__ == "__main__":
    app.run(debug=True)