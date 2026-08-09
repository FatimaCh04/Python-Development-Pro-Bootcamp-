import os

# Set required environment variables at the pytest session level.
# This runs before any test module is collected or imported,
# preventing ValueError from config.py when SECRET_KEY is absent.
os.environ.setdefault('SECRET_KEY', 'ci-test-secret-key')
os.environ.setdefault('APP_NAME', 'DockFlow')
os.environ.setdefault('APP_VERSION', '1.0.0')
os.environ.setdefault('FLASK_ENV', 'testing')
