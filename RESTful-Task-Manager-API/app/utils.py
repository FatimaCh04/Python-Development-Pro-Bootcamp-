from flask import jsonify
from marshmallow import ValidationError


def success_response(data: dict | list, message: str = "Success", status_code: int = 200):
    """Return a standardised JSON success response."""
    return jsonify({"status": "success", "message": message, "data": data}), status_code


def error_response(message: str, status_code: int, errors: dict | None = None):
    """Return a standardised JSON error response."""
    body = {"status": "error", "message": message, "status_code": status_code}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def paginate_query(query, page: int, per_page: int):
    """
    Apply pagination to a SQLAlchemy query.

    Returns a tuple of (items, pagination_meta).
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
    return pagination.items, meta


def validate_schema(schema_instance, data: dict):
    """
    Validate *data* against the given Marshmallow schema instance.

    Returns (loaded_data, None) on success, or (None, error_response) on failure.
    """
    try:
        loaded = schema_instance.load(data)
        return loaded, None
    except ValidationError as exc:
        return None, error_response(
            "Validation failed.",
            400,
            errors=exc.messages,
        )
