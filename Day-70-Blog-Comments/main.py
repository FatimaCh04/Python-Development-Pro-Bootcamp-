from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "change-this-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# LOGIN MANAGER
# =========================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = "Please login to continue."


@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# =========================================================
# USER MODEL
# =========================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    posts = db.relationship(
        "BlogPost",
        back_populates="author",
        cascade="all, delete-orphan"
    )

    comments = db.relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan"
    )


# =========================================================
# BLOG POST MODEL
# =========================================================

class BlogPost(db.Model):

    __tablename__ = "blog_posts"

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

    image_url = db.Column(
        db.String(500),
        nullable=False
    )

    created_at = db.Column(
        db.String(50),
        nullable=False
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    author = db.relationship(
        "User",
        back_populates="posts"
    )

    comments = db.relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )


# =========================================================
# COMMENT MODEL — DAY 70
# =========================================================

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    text = db.Column(
        db.Text,
        nullable=False
    )

    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("blog_posts.id"),
        nullable=False
    )

    author = db.relationship(
        "User",
        back_populates="comments"
    )

    post = db.relationship(
        "BlogPost",
        back_populates="comments"
    )


# =========================================================
# DATABASE
# =========================================================

with app.app_context():
    db.create_all()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    posts = BlogPost.query.order_by(
        BlogPost.id.desc()
    ).all()

    return render_template(
        "index.html",
        posts=posts
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill in all fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "This email is already registered.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(
                password
            )
        )

        db.session.add(new_user)

        db.session.commit()

        flash(
            "Account created successfully!",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user is None:

            flash(
                "No account found.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        if not check_password_hash(
            user.password_hash,
            password
        ):

            flash(
                "Incorrect password.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        login_user(user)

        return redirect(
            url_for("home")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("home")
    )


# =========================================================
# VIEW POST
# =========================================================

@app.route("/post/<int:post_id>")
def view_post(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    return render_template(
        "post.html",
        post=post
    )


# =========================================================
# CREATE POST
# =========================================================

@app.route(
    "/new-post",
    methods=["GET", "POST"]
)
@login_required
def new_post():

    if request.method == "POST":

        post = BlogPost(
            title=request.form["title"].strip(),
            subtitle=request.form["subtitle"].strip(),
            body=request.form["body"].strip(),
            image_url=request.form["image_url"].strip(),
            created_at=request.form["created_at"].strip(),
            author_id=current_user.id
        )

        db.session.add(post)

        db.session.commit()

        return redirect(
            url_for(
                "view_post",
                post_id=post.id
            )
        )

    return render_template(
        "make-post.html"
    )


# =========================================================
# EDIT POST
# =========================================================

@app.route(
    "/edit-post/<int:post_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_post(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    if (
        post.author_id != current_user.id
        and current_user.id != 1
    ):

        flash(
            "You cannot edit this post.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        post.title = request.form["title"].strip()

        post.subtitle = request.form["subtitle"].strip()

        post.body = request.form["body"].strip()

        post.image_url = request.form["image_url"].strip()

        post.created_at = request.form["created_at"].strip()

        db.session.commit()

        return redirect(
            url_for(
                "view_post",
                post_id=post.id
            )
        )

    return render_template(
        "make-post.html",
        post=post
    )


# =========================================================
# DELETE POST
# =========================================================

@app.route(
    "/delete-post/<int:post_id>"
)
@login_required
def delete_post(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    if (
        post.author_id != current_user.id
        and current_user.id != 1
    ):

        flash(
            "You cannot delete this post.",
            "danger"
        )

        return redirect(
            url_for("home")
        )

    db.session.delete(post)

    db.session.commit()

    return redirect(
        url_for("home")
    )


# =========================================================
# ADD COMMENT — MAIN DAY 70 FEATURE
# =========================================================

@app.route(
    "/post/<int:post_id>/comment",
    methods=["POST"]
)
@login_required
def add_comment(post_id):

    post = db.get_or_404(
        BlogPost,
        post_id
    )

    comment_text = request.form.get(
        "comment",
        ""
    ).strip()

    if not comment_text:

        flash(
            "Comment cannot be empty.",
            "danger"
        )

        return redirect(
            url_for(
                "view_post",
                post_id=post.id
            )
        )

    comment = Comment(
        text=comment_text,
        author_id=current_user.id,
        post_id=post.id
    )

    db.session.add(comment)

    db.session.commit()

    flash(
        "Comment added successfully!",
        "success"
    )

    return redirect(
        url_for(
            "view_post",
            post_id=post.id
        )
    )


# =========================================================
# DELETE COMMENT
# =========================================================

@app.route(
    "/delete-comment/<int:comment_id>"
)
@login_required
def delete_comment(comment_id):

    comment = db.get_or_404(
        Comment,
        comment_id
    )

    if (
        comment.author_id != current_user.id
        and current_user.id != 1
    ):

        flash(
            "You cannot delete this comment.",
            "danger"
        )

        return redirect(
            url_for(
                "view_post",
                post_id=comment.post_id
            )
        )

    post_id = comment.post_id

    db.session.delete(comment)

    db.session.commit()

    return redirect(
        url_for(
            "view_post",
            post_id=post_id
        )
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)