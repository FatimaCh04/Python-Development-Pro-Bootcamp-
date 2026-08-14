from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///blog.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================================
# BLOG POST MODEL
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

    date = db.Column(
        db.String(50),
        nullable=False
    )

    image_url = db.Column(
        db.String(500),
        nullable=False
    )


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

with app.app_context():

    db.create_all()

    if BlogPost.query.count() == 0:

        sample_posts = [

            BlogPost(
                title="My Python Journey",
                subtitle="Learning Python one project at a time",
                body="""
                Python has become an exciting part of my
                development journey. Every day I learn
                something new and build projects that
                improve my programming skills.
                """,
                author="Fatima",
                date="August 14, 2026",
                image_url=(
                    "https://images.unsplash.com/"
                    "photo-1515879218367-8466d910aaa4"
                )
            ),

            BlogPost(
                title="Why I Love Coding",
                subtitle="Turning ideas into real applications",
                body="""
                Coding allows me to transform ideas into
                useful applications. Building projects is
                one of the best ways to understand concepts
                and improve problem-solving skills.
                """,
                author="Fatima",
                date="August 14, 2026",
                image_url=(
                    "https://images.unsplash.com/"
                    "photo-1498050108023-c5249f4df085"
                )
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

@app.route(
    "/post/<int:post_id>"
)
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

@app.route(
    "/create-post",
    methods=["GET", "POST"]
)
def create_post():

    if request.method == "POST":

        new_post = BlogPost(

            title=request.form["title"],

            subtitle=request.form["subtitle"],

            body=request.form["body"],

            author=request.form["author"],

            date=request.form["date"],

            image_url=request.form["image_url"]

        )

        db.session.add(new_post)

        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template(
        "create-post.html"
    )


# ==========================================
# EDIT POST
# ==========================================

@app.route(
    "/edit/<int:post_id>",
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

        post.date = request.form["date"]

        post.image_url = request.form["image_url"]

        db.session.commit()

        return redirect(
            url_for(
                "show_post",
                post_id=post.id
            )
        )

    return render_template(
        "create-post.html",
        post=post
    )


# ==========================================
# DELETE POST
# ==========================================

@app.route(
    "/delete/<int:post_id>",
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
# RUN
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )