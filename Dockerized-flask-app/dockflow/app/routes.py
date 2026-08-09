from flask import Blueprint, jsonify, current_app

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "success",
        "message": "DockFlow API is running"
    })

@bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy"
    })

@bp.route('/api/info', methods=['GET'])
def info():
    return jsonify({
        "application": current_app.config.get('APP_NAME'),
        "version": current_app.config.get('APP_VERSION'),
        "environment": current_app.config.get('FLASK_ENV')
    })
