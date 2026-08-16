"""Flask application entry point."""
from app import create_app
import os

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print(f"""
    ╔════════════════════════════════════════╗
    ║      Field & Form Backend API          ║
    ╠════════════════════════════════════════╣
    ║  Running on http://{host}:{port}       ║
    ║  Environment: {os.getenv('FLASK_ENV', 'development'):20s}  ║
    ╚════════════════════════════════════════╝
    """)
    
    app.run(host=host, port=port, debug=debug)
