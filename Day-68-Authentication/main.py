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
    UserMixin,
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


app = Flask(__name__)

# ==========================================
# APP CONFIGURATION
# ==========================================

app.config["SECRET_KEY"] = "day-68-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///users.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ==========================================
# DATABASE
# ==========================================

db = SQLAlchemy(app)


# ==========================================
# LOGIN MANAGER
# ==========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ==========================================
# USER MODEL
# ==========================================

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


# ==========================================
# CREATE DATABASE
# ==========================================

with app.app_context():

    db.create_all()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# REGISTER
# ==========================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("secrets")
        )

    if request.method == "POST":

        name = request.form["name"].strip()

        email = request.form["email"].strip().lower()

        password = request.form["password"]

        confirm_password = request.form[
            "confirm_password"
        ]


        # Validate fields

        if not name or not email or not password:

            flash(
                "Please fill in all fields.",
                "danger"
            )

            return redirect(
                url_for("register")
            )


        # Check passwords

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("register")
            )


        # Check existing user

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


        # Hash password

        hashed_password = generate_password_hash(
            password,
            method="pbkdf2:sha256"
        )


        # Create user

        new_user = User(

            name=name,

            email=email,

            password=hashed_password

        )


        db.session.add(new_user)

        db.session.commit()


        flash(
            "Account created successfully! Please log in.",
            "success"
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ==========================================
# LOGIN
# ==========================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("secrets")
        )


    if request.method == "POST":

        email = request.form["email"].strip().lower()

        password = request.form["password"]


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


        flash(
            "Login successful!",
            "success"
        )


        next_page = request.args.get("next")


        if next_page:

            return redirect(next_page)


        return redirect(
            url_for("secrets")
        )


    return render_template(
        "login.html"
    )


# ==========================================
# PROTECTED PAGE
# ==========================================

@app.route("/secrets")
@login_required
def secrets():

    return render_template(
        "secrets.html"
    )


# ==========================================
# LOGOUT
# ==========================================

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


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )