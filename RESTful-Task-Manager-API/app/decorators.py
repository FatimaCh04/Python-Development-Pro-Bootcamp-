from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User


def admin_required(fn):
    """Decorator that allows only users with the 'admin' role to access the endpoint."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "User not found.", "status_code": 404}), 404
        if not user.is_admin():
            return (
                jsonify(
                    {
                        "error": "Admin privileges required.",
                        "status_code": 403,
                    }
                ),
                403,
            )
        return fn(*args, **kwargs)

    return wrapper


def jwt_required_with_identity(fn):
    """Decorator that validates JWT and injects the User object as 'current_user'."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if user is None:
            return jsonify({"error": "User not found.", "status_code": 404}), 404
        return fn(*args, current_user=user, **kwargs)

    return wrapper
