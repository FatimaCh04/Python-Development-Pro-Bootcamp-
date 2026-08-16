"""
Application factory for Pulse backend.
"""
import os
from datetime import timedelta
from flask import Flask, request
from .extensions import db, migrate, jwt, bcrypt, cors


def create_app(config_object=None):
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///pulse_dev.db"
    ).replace(
        "postgres://", "postgresql://"  # Render uses legacy postgres:// scheme
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    # Flask-JWT-Extended requires timedelta, not int
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_EXPIRES", 900))
    )
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
        seconds=int(os.environ.get("JWT_REFRESH_EXPIRES", 2592000))
    )

    # S3 / AWS settings read from env; no defaults for secrets
    app.config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    app.config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    app.config["AWS_S3_BUCKET"] = os.environ.get("AWS_S3_BUCKET")
    app.config["AWS_REGION"] = os.environ.get("AWS_REGION", "us-east-1")

    # Accept comma-separated origins, e.g. "http://localhost:5173,https://pulse.vercel.app"
    _cors_origins_raw = os.environ.get("CORS_ORIGIN", "http://localhost:5173,http://localhost:4173")
    app.config["CORS_ORIGINS"] = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

    if config_object:
        app.config.from_object(config_object)

    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    # Flask-CORS: allow all /api/* routes from the configured origins.
    # Setting vary_header ensures browsers don't cache the wrong CORS response.
    cors.init_app(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        expose_headers=["Content-Type", "Authorization"],
        vary_header=True,
    )

    # ------------------------------------------------------------------
    # Explicit OPTIONS handler — ensures preflight is handled before
    # JWT middleware can reject it with 401.
    # ------------------------------------------------------------------
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            return response

    # ------------------------------------------------------------------
    # JWT error handlers — return JSON, not HTML
    # ------------------------------------------------------------------

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"error": "token_expired", "message": "Token has expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {"error": "invalid_token", "message": str(error)}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {"error": "authorization_required", "message": str(error)}, 401

    # ------------------------------------------------------------------
    # Blueprints
    # ------------------------------------------------------------------
    from .routes.auth import auth_bp
    from .routes.posts import posts_bp
    from .routes.comments import comments_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(posts_bp, url_prefix="/api/posts")
    app.register_blueprint(comments_bp, url_prefix="/api/posts")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # ------------------------------------------------------------------
    # Health-check
    # ------------------------------------------------------------------
    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app
