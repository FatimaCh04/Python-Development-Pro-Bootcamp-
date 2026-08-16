"""
Comments routes
---------------
POST /api/posts/<id>/comments  – add a comment (or reply if parent_id provided)
GET  /api/posts/<id>/comments  – list all top-level comments with nested replies
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Post, Comment

comments_bp = Blueprint("comments", __name__)


# ---------------------------------------------------------------------------
# POST /api/posts/<id>/comments
# ---------------------------------------------------------------------------
@comments_bp.post("/<int:post_id>/comments")
@jwt_required()
def add_comment(post_id):
    current_user_id = int(get_jwt_identity())

    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    parent_id = data.get("parent_id")  # null → top-level comment

    # Validate parent_id belongs to the same post
    if parent_id is not None:
        parent = db.session.get(Comment, int(parent_id))
        if not parent or parent.post_id != post_id:
            return jsonify({"error": "Parent comment not found on this post"}), 404

    comment = Comment(
        post_id=post_id,
        user_id=current_user_id,
        parent_id=parent_id,
        content=content,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({"comment": comment.to_dict()}), 201


# ---------------------------------------------------------------------------
# GET /api/posts/<id>/comments
# ---------------------------------------------------------------------------
@comments_bp.get("/<int:post_id>/comments")
@jwt_required()
def get_comments(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    # Only fetch top-level comments; replies are nested via to_dict()
    top_level = (
        Comment.query
        .filter_by(post_id=post_id, parent_id=None)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return jsonify({"comments": [c.to_dict() for c in top_level]}), 200
