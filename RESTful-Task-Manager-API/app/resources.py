from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app.extensions import db, limiter
from app.models import Task, TaskStatus, TaskPriority, User, UserRole
from app.schemas import TaskCreateSchema, TaskUpdateSchema, TaskQuerySchema
from app.utils import success_response, error_response, paginate_query, validate_schema

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

task_create_schema = TaskCreateSchema()
task_update_schema = TaskUpdateSchema()
task_query_schema = TaskQuerySchema()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_current_user():
    """Return the User record for the JWT identity, or None."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def _apply_filters_and_sort(query, params: dict, user_id: int | None = None):
    """Apply filtering, searching, and sorting to a Task query."""
    if user_id is not None:
        query = query.filter(Task.user_id == user_id)

    if params.get("status"):
        query = query.filter(Task.status == TaskStatus(params["status"]))

    if params.get("priority"):
        query = query.filter(Task.priority == TaskPriority(params["priority"]))

    if params.get("search"):
        term = f"%{params['search']}%"
        query = query.filter(
            or_(
                Task.title.ilike(term),
                Task.description.ilike(term),
            )
        )

    sort = params.get("sort", "newest")
    if sort == "newest":
        query = query.order_by(Task.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Task.created_at.asc())
    elif sort == "due_date":
        query = query.order_by(Task.due_date.asc().nullslast())

    return query


# ---------------------------------------------------------------------------
# Task CRUD endpoints
# ---------------------------------------------------------------------------

@tasks_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("100 per hour")
def create_task():
    """
    Create a new task for the authenticated user.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - title
          properties:
            title:
              type: string
              example: Buy groceries
            description:
              type: string
              example: Milk, eggs, bread
            status:
              type: string
              enum: [pending, in_progress, completed, cancelled]
              example: pending
            priority:
              type: string
              enum: [low, medium, high, critical]
              example: medium
            due_date:
              type: string
              format: date-time
              example: "2025-12-31T23:59:59"
    responses:
      201:
        description: Task created successfully.
      400:
        description: Validation error.
      401:
        description: Unauthorised – missing or invalid JWT.
      500:
        description: Internal server error.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be valid JSON.", 400)

    data, err = validate_schema(task_create_schema, json_data)
    if err:
        return err

    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)

    try:
        task = Task(
            title=data["title"],
            description=data.get("description"),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "medium")),
            due_date=data.get("due_date"),
            user_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response("Failed to create task. Please try again.", 500)

    return success_response(task.to_dict(), "Task created successfully.", 201)


@tasks_bp.route("", methods=["GET"])
@jwt_required()
@limiter.limit("100 per hour")
def list_tasks():
    """
    List tasks for the authenticated user with filtering, searching, sorting, and pagination.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
      - in: query
        name: status
        type: string
        enum: [pending, in_progress, completed, cancelled]
      - in: query
        name: priority
        type: string
        enum: [low, medium, high, critical]
      - in: query
        name: search
        type: string
        description: Search in title and description.
      - in: query
        name: sort
        type: string
        enum: [newest, oldest, due_date]
        default: newest
    responses:
      200:
        description: Paginated list of tasks.
      400:
        description: Invalid query parameters.
      401:
        description: Unauthorised.
    """
    params, err = validate_schema(task_query_schema, request.args.to_dict())
    if err:
        return err

    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)

    # Admins see all tasks; regular users see only their own
    owner_id = None if current_user.is_admin() else current_user.id

    query = Task.query
    query = _apply_filters_and_sort(query, params, user_id=owner_id)
    items, meta = paginate_query(query, params["page"], params["per_page"])

    return success_response(
        {"tasks": [t.to_dict() for t in items], "pagination": meta},
        "Tasks retrieved successfully.",
    )


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
@limiter.limit("100 per hour")
def get_task(task_id: int):
    """
    Retrieve a single task by ID.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
    responses:
      200:
        description: Task retrieved successfully.
      401:
        description: Unauthorised.
      403:
        description: Forbidden – task belongs to another user.
      404:
        description: Task not found.
    """
    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)

    task = Task.query.get(task_id)
    if task is None:
        return error_response(f"Task with id={task_id} not found.", 404)

    if not current_user.is_admin() and task.user_id != current_user.id:
        return error_response("You do not have permission to view this task.", 403)

    return success_response(task.to_dict(), "Task retrieved successfully.")


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
@limiter.limit("100 per hour")
def update_task(task_id: int):
    """
    Update a task by ID. Users can only update their own tasks.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            status:
              type: string
              enum: [pending, in_progress, completed, cancelled]
            priority:
              type: string
              enum: [low, medium, high, critical]
            due_date:
              type: string
              format: date-time
    responses:
      200:
        description: Task updated successfully.
      400:
        description: Validation error.
      401:
        description: Unauthorised.
      403:
        description: Forbidden.
      404:
        description: Task not found.
      500:
        description: Internal server error.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return error_response("Request body must be valid JSON.", 400)

    data, err = validate_schema(task_update_schema, json_data)
    if err:
        return err

    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)

    task = Task.query.get(task_id)
    if task is None:
        return error_response(f"Task with id={task_id} not found.", 404)

    if not current_user.is_admin() and task.user_id != current_user.id:
        return error_response("You do not have permission to update this task.", 403)

    try:
        if "title" in data:
            task.title = data["title"]
        if "description" in data:
            task.description = data["description"]
        if "status" in data:
            task.status = TaskStatus(data["status"])
        if "priority" in data:
            task.priority = TaskPriority(data["priority"])
        if "due_date" in data:
            task.due_date = data["due_date"]
        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response("Failed to update task. Please try again.", 500)

    return success_response(task.to_dict(), "Task updated successfully.")


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
@limiter.limit("100 per hour")
def delete_task(task_id: int):
    """
    Delete a task by ID. Users can only delete their own tasks. Admins can delete any task.
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
    responses:
      200:
        description: Task deleted successfully.
      401:
        description: Unauthorised.
      403:
        description: Forbidden.
      404:
        description: Task not found.
      500:
        description: Internal server error.
    """
    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)

    task = Task.query.get(task_id)
    if task is None:
        return error_response(f"Task with id={task_id} not found.", 404)

    if not current_user.is_admin() and task.user_id != current_user.id:
        return error_response("You do not have permission to delete this task.", 403)

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response("Failed to delete task. Please try again.", 500)

    return success_response({}, "Task deleted successfully.")


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@limiter.limit("100 per hour")
def admin_list_users():
    """
    [Admin] List all registered users with pagination.
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
    responses:
      200:
        description: List of users.
      401:
        description: Unauthorised.
      403:
        description: Admin privileges required.
    """
    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)
    if not current_user.is_admin():
        return error_response("Admin privileges required.", 403)

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    query = User.query.order_by(User.created_at.desc())
    items, meta = paginate_query(query, page, per_page)

    return success_response(
        {"users": [u.to_dict() for u in items], "pagination": meta},
        "Users retrieved successfully.",
    )


@admin_bp.route("/tasks", methods=["GET"])
@jwt_required()
@limiter.limit("100 per hour")
def admin_list_all_tasks():
    """
    [Admin] List all tasks across all users with filtering, searching, sorting, and pagination.
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 10
      - in: query
        name: status
        type: string
        enum: [pending, in_progress, completed, cancelled]
      - in: query
        name: priority
        type: string
        enum: [low, medium, high, critical]
      - in: query
        name: search
        type: string
      - in: query
        name: sort
        type: string
        enum: [newest, oldest, due_date]
        default: newest
    responses:
      200:
        description: Paginated list of all tasks.
      401:
        description: Unauthorised.
      403:
        description: Admin privileges required.
    """
    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)
    if not current_user.is_admin():
        return error_response("Admin privileges required.", 403)

    params, err = validate_schema(task_query_schema, request.args.to_dict())
    if err:
        return err

    query = Task.query
    query = _apply_filters_and_sort(query, params, user_id=None)
    items, meta = paginate_query(query, params["page"], params["per_page"])

    return success_response(
        {"tasks": [t.to_dict() for t in items], "pagination": meta},
        "All tasks retrieved successfully.",
    )


@admin_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
@limiter.limit("100 per hour")
def admin_delete_task(task_id: int):
    """
    [Admin] Delete any task by ID.
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
    responses:
      200:
        description: Task deleted successfully.
      401:
        description: Unauthorised.
      403:
        description: Admin privileges required.
      404:
        description: Task not found.
      500:
        description: Internal server error.
    """
    current_user = _get_current_user()
    if current_user is None:
        return error_response("User not found.", 404)
    if not current_user.is_admin():
        return error_response("Admin privileges required.", 403)

    task = Task.query.get(task_id)
    if task is None:
        return error_response(f"Task with id={task_id} not found.", 404)

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response("Failed to delete task. Please try again.", 500)

    return success_response({}, "Task deleted successfully by admin.")
