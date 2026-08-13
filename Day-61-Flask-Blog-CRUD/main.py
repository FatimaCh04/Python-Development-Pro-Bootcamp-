from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================================
# BLOG MODEL
# ==========================================

class BlogPost(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    subtitle = db.Column(
        db.String(300),
        nullable=False
    )

    body = db.Column(
        db.Text,
        nullable=False
    )

    author = db.Column(
        db.String(100),
        nullable=False
    )


# ==========================================
# CREATE DATABASE + SAMPLE DATA
# ==========================================

with app.app_context():

    db.create_all()

    if BlogPost.query.count() == 0:

        posts = [

            BlogPost(
                title="My Python Journey",
                subtitle="Learning Python every day",
                body=(
                    "I am learning Python through practical "
                    "projects and daily coding practice."
                ),
                author="Fatima"
            ),

            BlogPost(
                title="Learning Flask",
                subtitle="Building websites with Python",
                body=(
                    "Flask is a lightweight Python web framework "
                    "that makes it easy to build web applications."
                ),
                author="Fatima"
            )

        ]

        db.session.add_all(posts)
        db.session.commit()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    posts = BlogPost.query.order_by(
        BlogPost.id.desc()
    ).all()

    return render_template(
        "index.html",
        posts=posts
    )


# ==========================================
# SINGLE POST
# ==========================================

@app.route("/post/<int:post_id>")
def show_post(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    return render_template(
        "post.html",
        post=post
    )


# ==========================================
# CREATE POST
# ==========================================

@app.route("/create-post", methods=["GET", "POST"])
def create_post():

    if request.method == "POST":

        title = request.form["title"]
        subtitle = request.form["subtitle"]
        body = request.form["body"]
        author = request.form["author"]

        new_post = BlogPost(
            title=title,
            subtitle=subtitle,
            body=body,
            author=author
        )

        db.session.add(new_post)
        db.session.commit()

        return redirect(
            url_for(
                "show_post",
                post_id=new_post.id
            )
        )

    return render_template(
        "create-post.html"
    )


# ==========================================
# EDIT POST
# ==========================================

@app.route(
    "/edit-post/<int:post_id>",
    methods=["GET", "POST"]
)
def edit_post(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    if request.method == "POST":

        post.title = request.form["title"]
        post.subtitle = request.form["subtitle"]
        post.body = request.form["body"]
        post.author = request.form["author"]

        db.session.commit()

        return redirect(
            url_for(
                "show_post",
                post_id=post.id
            )
        )

    return render_template(
        "edit-post.html",
        post=post
    )


# ==========================================
# DELETE POST
# ==========================================

@app.route(
    "/delete-post/<int:post_id>",
    methods=["POST"]
)
def delete_post(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    db.session.delete(post)
    db.session.commit()

    return redirect(
        url_for("home")
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