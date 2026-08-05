import os
from flask import Flask, jsonify
from dotenv import load_dotenv

from app.config import config_map
from app.extensions import db, migrate, jwt, limiter, swagger

load_dotenv()


def create_app(config_name: str | None = None) -> Flask:
    """Application factory."""

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Load config
    cfg = config_map.get(config_name, config_map["default"])
    app.config.from_object(cfg)

    # Initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    swagger.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.resources import tasks_bp, admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(admin_bp)

    # ------------------------------------------------------------------
    # JWT error handlers
    # ------------------------------------------------------------------

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"status": "error", "message": "Token has expired.", "status_code": 401}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"status": "error", "message": "Invalid token.", "status_code": 401}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"status": "error", "message": "Authorization token is missing.", "status_code": 401}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"status": "error", "message": "Token has been revoked.", "status_code": 401}), 401

    # ------------------------------------------------------------------
    # HTTP error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"status": "error", "message": "Bad request.", "status_code": 400}), 400

    @app.errorhandler(401)
    def unauthorised(e):
        return jsonify({"status": "error", "message": "Unauthorised.", "status_code": 401}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"status": "error", "message": "Forbidden.", "status_code": 403}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Resource not found.", "status_code": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"status": "error", "message": "Method not allowed.", "status_code": 405}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"status": "error", "message": "Rate limit exceeded. Try again later.", "status_code": 429}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "message": "Internal server error.", "status_code": 500}), 500

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "RESTful Task Manager API is running."}), 200

    return app
