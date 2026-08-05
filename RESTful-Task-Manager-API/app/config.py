import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/task_manager_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # Rate Limiting
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # Swagger
    SWAGGER = {
        "title": "RESTful Task Manager API",
        "uiversion": 3,
        "version": "1.0.0",
        "description": (
            "A production-ready RESTful Task Manager API built with Flask, "
            "Flask-JWT-Extended, SQLAlchemy, and Marshmallow. "
            "Supports user authentication, role-based access control, "
            "task CRUD operations, filtering, pagination, and sorting."
        ),
        "termsOfService": "",
        "contact": {
            "name": "API Support",
            "email": "support@taskmanager.com",
        },
        "license": {
            "name": "MIT",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": (
                    "JWT Authorization header using the Bearer scheme. "
                    'Enter: **Bearer &lt;your_token&gt;**'
                ),
            }
        },
        "security": [{"Bearer": []}],
    }

    # Pagination defaults
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 10
    MAX_PER_PAGE = 100


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=300)
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
