"""
Auth routes
-----------
POST /api/auth/signup   – create account, return tokens + user
POST /api/auth/login    – verify credentials, return tokens + user
POST /api/auth/refresh  – exchange refresh token for new access token
GET  /api/auth/me       – return current user (requires access token)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from ..extensions import db, bcrypt
from ..models import User

auth_bp = Blueprint("auth", __name__)


def _user_tokens(user: User):
    """Return both tokens and the user dict in a single response body."""
    identity = str(user.id)
    return {
        "access_token": create_access_token(identity=identity),
        "refresh_token": create_refresh_token(identity=identity),
        "user": user.to_dict(),
    }


# ---------------------------------------------------------------------------
# POST /api/auth/signup
# ---------------------------------------------------------------------------
@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists"}), 409

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # First registered user becomes admin for convenience during development.
    role = "admin" if User.query.count() == 0 else "user"

    user = User(name=name, email=email, password_hash=pw_hash, role=role)
    db.session.add(user)
    db.session.commit()

    return jsonify(_user_tokens(user)), 201


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------
@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify(_user_tokens(user)), 200


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------
@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "access_token": create_access_token(identity=identity),
        "user": user.to_dict(),
    }), 200


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------
@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
