import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration variables."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pulsechat-super-secret-dev-key')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Store the database inside the database/ folder
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'chat.db')

    # Security limits
    MAX_USERNAME_LEN = 30
    MAX_ROOM_LEN = 30
    MAX_MESSAGE_LEN = 1000
