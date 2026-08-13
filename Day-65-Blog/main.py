from flask import Flask, render_template

app = Flask(__name__)


posts = [
    {
        "id": 1,
        "title": "My Python Journey",
        "subtitle": "Learning Python one day at a time",
        "author": "Fatima",
        "date": "August 2026",
        "image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4",
        "body": """
        Learning Python has been an exciting journey.
        Every day I am learning something new and
        building projects to improve my skills.
        """
    },
    {
        "id": 2,
        "title": "Why I Love Coding",
        "subtitle": "Turning ideas into real applications",
        "author": "Fatima",
        "date": "August 2026",
        "image": "https://images.unsplash.com/photo-1498050108023-c5249f4df085",
        "body": """
        Coding allows me to turn ideas into useful
        applications. The more I practice, the more
        confident I become.
        """
    }
]


@app.route("/")
def home():
    return render_template(
        "index.html",
        posts=posts
    )


@app.route("/post/<int:post_id>")
def post(post_id):

    selected_post = None

    for item in posts:
        if item["id"] == post_id:
            selected_post = item
            break

    return render_template(
        "post.html",
        post=selected_post
    )


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)