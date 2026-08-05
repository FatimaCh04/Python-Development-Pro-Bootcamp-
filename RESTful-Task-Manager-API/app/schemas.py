from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load
from app.models import TaskStatus, TaskPriority


# ---------------------------------------------------------------------------
# Reusable validators
# ---------------------------------------------------------------------------

VALID_STATUSES = [s.value for s in TaskStatus]
VALID_PRIORITIES = [p.value for p in TaskPriority]
VALID_SORT_FIELDS = ["newest", "oldest", "due_date"]


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class RegisterSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=80, error="Username must be between 3 and 80 characters."),
            validate.Regexp(
                r"^[a-zA-Z0-9_]+$",
                error="Username may only contain letters, numbers, and underscores.",
            ),
        ],
    )
    email = fields.Email(
        required=True,
        error_messages={"validator_failed": "A valid email address is required."},
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128, error="Password must be at least 8 characters."),
    )
    role = fields.Str(
        load_default="user",
        validate=validate.OneOf(
            ["admin", "user"],
            error="Role must be 'admin' or 'user'.",
        ),
    )

    @validates("password")
    def validate_password_strength(self, value: str) -> str:
        if not any(c.isupper() for c in value):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValidationError("Password must contain at least one digit.")
        return value

    @pre_load
    def strip_strings(self, data: dict, **kwargs) -> dict:
        stripped = {}
        for k, v in data.items():
            stripped[k] = v.strip() if isinstance(v, str) else v
        return stripped


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)

    @pre_load
    def strip_strings(self, data: dict, **kwargs) -> dict:
        stripped = {}
        for k, v in data.items():
            stripped[k] = v.strip() if isinstance(v, str) else v
        return stripped


# ---------------------------------------------------------------------------
# Task schemas
# ---------------------------------------------------------------------------

class TaskCreateSchema(Schema):
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200, error="Title must be between 1 and 200 characters."),
    )
    description = fields.Str(load_default=None, allow_none=True)
    status = fields.Str(
        load_default="pending",
        validate=validate.OneOf(VALID_STATUSES, error=f"Status must be one of: {VALID_STATUSES}."),
    )
    priority = fields.Str(
        load_default="medium",
        validate=validate.OneOf(VALID_PRIORITIES, error=f"Priority must be one of: {VALID_PRIORITIES}."),
    )
    due_date = fields.DateTime(
        load_default=None,
        allow_none=True,
        format="iso",
        error_messages={"invalid": "due_date must be a valid ISO 8601 datetime string."},
    )

    @pre_load
    def strip_strings(self, data: dict, **kwargs) -> dict:
        stripped = {}
        for k, v in data.items():
            stripped[k] = v.strip() if isinstance(v, str) else v
        return stripped


class TaskUpdateSchema(Schema):
    title = fields.Str(
        required=False,
        validate=validate.Length(min=1, max=200, error="Title must be between 1 and 200 characters."),
    )
    description = fields.Str(required=False, allow_none=True)
    status = fields.Str(
        required=False,
        validate=validate.OneOf(VALID_STATUSES, error=f"Status must be one of: {VALID_STATUSES}."),
    )
    priority = fields.Str(
        required=False,
        validate=validate.OneOf(VALID_PRIORITIES, error=f"Priority must be one of: {VALID_PRIORITIES}."),
    )
    due_date = fields.DateTime(
        required=False,
        allow_none=True,
        format="iso",
        error_messages={"invalid": "due_date must be a valid ISO 8601 datetime string."},
    )

    @pre_load
    def strip_strings(self, data: dict, **kwargs) -> dict:
        stripped = {}
        for k, v in data.items():
            stripped[k] = v.strip() if isinstance(v, str) else v
        return stripped


class TaskQuerySchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=10, validate=validate.Range(min=1, max=100))
    status = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(VALID_STATUSES + [None], error=f"status must be one of: {VALID_STATUSES}."),
    )
    priority = fields.Str(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(VALID_PRIORITIES + [None], error=f"priority must be one of: {VALID_PRIORITIES}."),
    )
    search = fields.Str(load_default=None, allow_none=True)
    sort = fields.Str(
        load_default="newest",
        validate=validate.OneOf(VALID_SORT_FIELDS, error=f"sort must be one of: {VALID_SORT_FIELDS}."),
    )
