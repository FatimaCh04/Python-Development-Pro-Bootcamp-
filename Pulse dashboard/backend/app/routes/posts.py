"""
Posts routes
------------
GET  /api/posts               – paginated feed (optional ?tag= filter, ?page=, ?per_page=)
POST /api/posts               – create post (multipart/form-data; image uploaded to S3)
POST /api/posts/<id>/like     – toggle like on a post
"""
import re
import uuid
import boto3
from botocore.exceptions import ClientError
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Post, Like, Hashtag, post_hashtags, User

posts_bp = Blueprint("posts", __name__)

_TAG_RE = re.compile(r"#([\w]+)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tags(text: str) -> list[str]:
    """Return unique lowercase tag strings (without #) found in text."""
    return list({m.lower() for m in _TAG_RE.findall(text)})


def _upsert_hashtags(tag_strings: list[str]) -> list[Hashtag]:
    """Get-or-create Hashtag rows for every tag string."""
    tags = []
    for t in tag_strings:
        existing = Hashtag.query.filter_by(tag=t).first()
        if existing:
            tags.append(existing)
        else:
            new_tag = Hashtag(tag=t)
            db.session.add(new_tag)
            tags.append(new_tag)
    return tags


def _upload_to_s3(file_obj, filename: str) -> str | None:
    """
    Upload a file-like object to S3.
    Returns a presigned URL (bucket is assumed private) or a public URL.
    Returns None if AWS credentials are not configured.
    """
    bucket = current_app.config.get("AWS_S3_BUCKET")
    region = current_app.config.get("AWS_REGION", "us-east-1")
    access_key = current_app.config.get("AWS_ACCESS_KEY_ID")
    secret_key = current_app.config.get("AWS_SECRET_ACCESS_KEY")

    if not all([bucket, access_key, secret_key]):
        # S3 not configured — skip upload, return None
        return None

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    key = f"posts/{uuid.uuid4().hex}.{ext}"

    s3 = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        s3.upload_fileobj(
            file_obj,
            bucket,
            key,
            ExtraArgs={"ContentType": file_obj.content_type or "image/jpeg"},
        )
        # Generate a presigned URL (valid 7 days); works for private buckets.
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=604800,
        )
        return url
    except ClientError as exc:
        current_app.logger.error("S3 upload failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# GET /api/posts
# ---------------------------------------------------------------------------
@posts_bp.get("")
@jwt_required()
def get_posts():
    current_user_id = int(get_jwt_identity())
    tag = request.args.get("tag", "").lstrip("#").lower().strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 20))))

    query = Post.query.order_by(Post.created_at.desc())

    if tag:
        query = (
            query
            .join(post_hashtags, Post.id == post_hashtags.c.post_id)
            .join(Hashtag, Hashtag.id == post_hashtags.c.hashtag_id)
            .filter(Hashtag.tag == tag)
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "posts": [p.to_dict(current_user_id=current_user_id) for p in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    }), 200


# ---------------------------------------------------------------------------
# POST /api/posts
# ---------------------------------------------------------------------------
@posts_bp.post("")
@jwt_required()
def create_post():
    current_user_id = int(get_jwt_identity())

    # Support both multipart/form-data (with image) and application/json
    if request.content_type and "multipart/form-data" in request.content_type:
        content = (request.form.get("content") or "").strip()
    else:
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"error": "content is required"}), 400

    image_url = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename:
            image_url = _upload_to_s3(file, file.filename)
            if image_url is None:
                # S3 not configured — store a placeholder so the client sees something
                image_url = None  # stays null; frontend handles gracefully

    tag_strings = _extract_tags(content)
    hashtags = _upsert_hashtags(tag_strings)

    post = Post(user_id=current_user_id, content=content, image_url=image_url)
    post.hashtags = hashtags
    db.session.add(post)
    db.session.commit()

    return jsonify({"post": post.to_dict(current_user_id=current_user_id)}), 201


# ---------------------------------------------------------------------------
# POST /api/posts/<id>/like  (toggle)
# ---------------------------------------------------------------------------
@posts_bp.post("/<int:post_id>/like")
@jwt_required()
def toggle_like(post_id):
    current_user_id = int(get_jwt_identity())

    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    existing = Like.query.filter_by(post_id=post_id, user_id=current_user_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(post_id=post_id, user_id=current_user_id))
        liked = True

    db.session.commit()
    db.session.refresh(post)

    return jsonify({"liked": liked, "likes": post.like_count}), 200
