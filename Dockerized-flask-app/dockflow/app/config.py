import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    APP_NAME = os.environ.get('APP_NAME', 'DockFlow')
    APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
