"""Flask extensions initialization."""
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from celery import Celery

# Initialize extensions (without app context)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()
celery = Celery(__name__)


def init_extensions(app):
    """Initialize Flask extensions with app context."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ------------------------------------------------------------------
    # JWT error callbacks
    #
    # flask-jwt-extended handles its own errors through JWTManager
    # callbacks, not through Flask's @app.errorhandler mechanism.
    # Without these, the library emits {"msg": "..."} with inconsistent
    # status codes (422 for malformed tokens) that differ from the rest
    # of the API which uses {"error": "..."} + 401.
    #
    # All four callbacks normalise the response to:
    #   {"error": "<human-readable reason>"}   HTTP 401
    # ------------------------------------------------------------------

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Access or refresh token has passed its expiry time."""
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        """Token is structurally malformed or has a bad signature.
        flask-jwt-extended defaults this to 422; we normalise to 401
        so the frontend only needs to handle one status code for auth
        failures."""
        return jsonify({'error': f'Invalid token: {reason}'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        """Request reached a @jwt_required() route with no token at all."""
        return jsonify({'error': 'Authentication required'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Token has been explicitly revoked (e.g. after logout, if a
        blocklist is implemented later)."""
        return jsonify({'error': 'Token has been revoked'}), 401

    # CORS — restrict to configured frontend URL
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config['FRONTEND_URL']}},
        supports_credentials=True,
    )

    mail.init_app(app)

    # Celery configuration (includes eager mode settings from config.py)
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_always_eager=app.config.get('CELERY_TASK_ALWAYS_EAGER', False),
        task_eager_propagates=app.config.get('CELERY_TASK_EAGER_PROPAGATES', True),
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
    )

    # Make every Celery task run inside a Flask app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery
