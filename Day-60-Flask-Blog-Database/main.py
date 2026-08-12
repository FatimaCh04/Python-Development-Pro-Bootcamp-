from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy


# ==========================================
# CREATE FLASK APP
# ==========================================

app = Flask(__name__)


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

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

    def __repr__(self):

        return f"<BlogPost {self.title}>"


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()


    # Add sample posts only if database is empty

    if BlogPost.query.count() == 0:

        sample_posts = [

            BlogPost(
                title="My Python Journey",
                subtitle="Learning Python one day at a time",
                body=(
                    "I started my Python journey by learning "
                    "the fundamentals and gradually moved toward "
                    "real-world projects."
                ),
                author="Fatima"
            ),

            BlogPost(
                title="Learning Flask",
                subtitle="Building web applications with Python",
                body=(
                    "Flask makes it possible to create web "
                    "applications using Python. Routes, templates "
                    "and Jinja make web development easier."
                ),
                author="Fatima"
            ),

            BlogPost(
                title="Why Practice Matters",
                subtitle="Consistency is the key to improvement",
                body=(
                    "Building projects regularly helps transform "
                    "programming concepts into practical skills."
                ),
                author="Fatima"
            )
        ]

        db.session.add_all(sample_posts)

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