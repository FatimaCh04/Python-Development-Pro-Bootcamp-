from flask import Flask, jsonify
from .config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not Found", "status_code": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({"error": "Method Not Allowed", "status_code": 405}), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal Server Error", "status_code": 500}), 500

    return app
