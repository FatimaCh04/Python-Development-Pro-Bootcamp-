"""
Admin routes  (role = "admin" required on every endpoint)
----------------------------------------------------------
DELETE /api/admin/posts/<id>   – hard-delete a post
GET    /api/admin/stats        – platform-level counts
GET    /api/admin/posts        – paginated list of ALL posts with author info
"""
from functools import wraps
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Post, User, Like, Comment

admin_bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------------------
# @admin_required decorator
# ---------------------------------------------------------------------------
def admin_required(fn):
    """
    Combines @jwt_required() with a role check.
    Must be applied AFTER @jwt_required() or used stand-alone (wraps jwt_required).
    Usage:  @admin_required   (no parentheses needed)
    """
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        user = db.session.get(User, int(identity))
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# DELETE /api/admin/posts/<id>
# ---------------------------------------------------------------------------
@admin_bp.delete("/posts/<int:post_id>")
@admin_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted", "post_id": post_id}), 200


# ---------------------------------------------------------------------------
# GET /api/admin/stats
# ---------------------------------------------------------------------------
@admin_bp.get("/stats")
@admin_required
def stats():
    total_posts = Post.query.count()
    total_users = User.query.count()
    total_likes = Like.query.count()
    total_comments = Comment.query.count()

    return jsonify({
        "total_posts": total_posts,
        "total_users": total_users,
        "total_likes": total_likes,
        "total_comments": total_comments,
    }), 200


# ---------------------------------------------------------------------------
# GET /api/admin/posts  (full feed for admin panel, no user-specific liked flag)
# ---------------------------------------------------------------------------
@admin_bp.get("/posts")
@admin_required
def list_all_posts():
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))

    pagination = (
        Post.query
        .order_by(Post.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    identity = get_jwt_identity()
    current_user_id = int(identity)

    return jsonify({
        "posts": [p.to_dict(current_user_id=current_user_id) for p in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    }), 200
