from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = "day88-secret-key-change-this"

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

INSTANCE_DIR.mkdir(exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{INSTANCE_DIR / 'users.db'}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):

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

    password = db.Column(
        db.String(255),
        nullable=False
    )


# ============================================================
# USER LOADER
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================
# DATABASE
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("secret")
        )


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


        if not name or not email or not password:

            flash(
                "All fields are required.",
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
                "An account with this email already exists.",
                "warning"
            )

            return redirect(
                url_for("login")
            )


        hashed_password = generate_password_hash(
            password,
            method="pbkdf2:sha256"
        )


        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )


        db.session.add(new_user)
        db.session.commit()


        login_user(new_user)


        return redirect(
            url_for("secret")
        )


    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("secret")
        )


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


        if not user:

            flash(
                "No account found with this email.",
                "danger"
            )

            return redirect(
                url_for("login")
            )


        if not check_password_hash(
            user.password,
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
            url_for("secret")
        )


    return render_template(
        "login.html"
    )


# ============================================================
# PROTECTED PAGE
# ============================================================

@app.route("/secret")
@login_required
def secret():

    return render_template(
        "secret.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )