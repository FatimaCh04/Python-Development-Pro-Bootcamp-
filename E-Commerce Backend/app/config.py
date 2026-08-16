"""Application configuration."""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database — defaults to SQLite so the app runs with zero extra installs
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///fieldform.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLite-safe pool options (PostgreSQL options removed from defaults)
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Stripe
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

    # Redis & Celery
    # When REDIS_URL is empty Celery runs in eager/synchronous mode (no broker needed)
    _redis_url = os.getenv('REDIS_URL') or None
    REDIS_URL = _redis_url
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL') or _redis_url or 'memory://'
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND') or _redis_url or 'cache+memory://'

    # If no Redis, run tasks synchronously so emails still work in development
    CELERY_TASK_ALWAYS_EAGER = _redis_url is None
    CELERY_TASK_EAGER_PROPAGATES = True

    # Email
    MAIL_SERVER = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('SMTP_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('SMTP_USER') or None
    MAIL_PASSWORD = os.getenv('SMTP_PASS') or None
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_FROM', 'noreply@fieldandform.com')
    # Suppress send errors when SMTP is not configured
    MAIL_SUPPRESS_SEND = not bool(os.getenv('SMTP_USER'))

    # Frontend
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


class DevelopmentConfig(Config):
    """Development configuration — verbose errors, SQLite, no Redis needed."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Override these in .env for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class TestingConfig(Config):
    """Testing configuration — in-memory SQLite."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CELERY_TASK_ALWAYS_EAGER = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
