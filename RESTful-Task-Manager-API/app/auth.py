from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from app.extensions import db, limiter
from app.models import User, UserRole
from app.schemas import RegisterSchema, LoginSchema
from app.utils import success_response, error_response, validate_schema

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
def register():
    """
    Register a new user.
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: johndoe
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: Secret123
            role:
              type: string
              enum: [user, admin]
              example: user
    responses:
      201:
        description: User registered successfully.
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: User registered successfully.
            data:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
                role:
                  type: string
                created_at:
                  type: string
      400:
        description: Validation error or duplicate user.
      500:
        description: Internal server error.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be valid JSON.", 400)

    data, err = validate_schema(register_schema, json_data)
    if err:
        return err

    if User.query.filter_by(email=data["email"]).first():
        return error_response("A user with that email already exists.", 400)

    if User.query.filter_by(username=data["username"]).first():
        return error_response("A user with that username already exists.", 400)

    try:
        role = UserRole(data.get("role", "user"))
        user = User(
            username=data["username"],
            email=data["email"],
            role=role,
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response("Failed to create user. Please try again.", 500)

    return success_response(user.to_dict(), "User registered successfully.", 201)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("20 per hour")
def login():
    """
    Log in and receive a JWT access token.
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: Secret123
    responses:
      200:
        description: Login successful.
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Login successful.
            data:
              type: object
              properties:
                access_token:
                  type: string
                user:
                  type: object
      400:
        description: Validation error.
      401:
        description: Invalid credentials.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be valid JSON.", 400)

    data, err = validate_schema(login_schema, json_data)
    if err:
        return err

    user = User.query.filter_by(email=data["email"]).first()
    if user is None or not user.check_password(data["password"]):
        return error_response("Invalid email or password.", 401)

    access_token = create_access_token(identity=str(user.id))

    return success_response(
        {"access_token": access_token, "user": user.to_dict()},
        "Login successful.",
        200,
    )
