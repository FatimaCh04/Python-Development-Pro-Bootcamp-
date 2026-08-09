import sys

# Flask-SocketIO works without eventlet on Python 3.13+
# using the built-in threading mode or simple-websocket instead
from flask import Flask, render_template
from flask_socketio import SocketIO

from config import Config
from utils.helpers import setup_logger
from services.database_service import DatabaseService
from services.redis_service import RedisService
from sockets.chat_events import register_socket_events

logger = setup_logger(__name__)

def create_app():
    """Application factory for PulseChat."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize services
    db_service = DatabaseService(app.config['DATABASE_PATH'])
    redis_service = RedisService(app.config['REDIS_URL'])
    
    if not db_service.initialize_database():
        logger.critical("Could not initialize database. Check permissions.")
        sys.exit(1)
        
    if not redis_service.is_available():
        logger.warning("Redis is not available. Using in-memory fallback for session tracking.")
        
    # Initialize SocketIO without Redis message_queue (uses threading mode)
    # This ensures full compatibility without requiring Redis or eventlet
    socketio = SocketIO(
        app,
        async_mode='threading',
        cors_allowed_origins="*"
    )
    
    # Register events
    register_socket_events(socketio, db_service, redis_service)
    
    # Routes
    @app.route('/')
    def index():
        return render_template('index.html')
        
    return app, socketio

app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
