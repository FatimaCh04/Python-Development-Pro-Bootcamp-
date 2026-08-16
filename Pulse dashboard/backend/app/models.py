"""
SQLAlchemy ORM models for Pulse.

Tables
------
users           – accounts with role-based access
posts           – user posts (optional S3 image)
comments        – threaded replies (self-referential parent_id)
likes           – unique per (post, user); supports toggle
hashtags        – normalised tag strings
post_hashtags   – M2M association between posts and hashtags
"""
from datetime import datetime, timezone
from .extensions import db

# ---------------------------------------------------------------------------
# Association table: post <-> hashtag  (no extra columns needed)
# ---------------------------------------------------------------------------
post_hashtags = db.Table(
    "post_hashtags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("hashtag_id", db.Integer, db.ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True),
)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # "user" | "admin"
    avatar_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    posts = db.relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    likes = db.relationship("Like", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "avatar_url": self.avatar_url
            or f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.email}",
            "created_at": self.created_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------
class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(1024), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    author = db.relationship("User", back_populates="posts")
    # All comments (including replies) on this post — used for cascade delete
    all_comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = db.relationship("Like", back_populates="post", cascade="all, delete-orphan")
    hashtags = db.relationship("Hashtag", secondary=post_hashtags, back_populates="posts")

    @property
    def like_count(self):
        return len(self.likes)

    def to_dict(self, current_user_id=None):
        liked = False
        if current_user_id is not None:
            liked = any(lk.user_id == current_user_id for lk in self.likes)
        return {
            "id": self.id,
            "author": {
                "id": self.author.id,
                "name": self.author.name,
                "handle": f"@{self.author.name.lower().replace(' ', '')}",
                "avatar": self.author.avatar_url
                or f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.author.email}",
            },
            "content": self.content,
            "image": self.image_url,
            "timestamp": _relative_time(self.created_at),
            "created_at": self.created_at.isoformat(),
            "likes": self.like_count,
            "liked": liked,
            "tags": [f"#{h.tag}" for h in self.hashtags],
            "comments": [],  # populated separately via GET /api/posts/:id/comments
        }


# ---------------------------------------------------------------------------
# Comment  (self-referential for nested replies)
# ---------------------------------------------------------------------------
class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = db.Column(
        db.Integer, db.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    author = db.relationship("User", back_populates="comments")
    post = db.relationship("Post", back_populates="all_comments")
    # Direct children of this comment
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Comment.created_at",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "author": {
                "id": self.author.id,
                "name": self.author.name,
                "avatar": self.author.avatar_url
                or f"https://api.dicebear.com/7.x/avataaars/svg?seed={self.author.email}",
            },
            "content": self.content,
            "timestamp": _relative_time(self.created_at),
            "created_at": self.created_at.isoformat(),
            "parent_id": self.parent_id,
            "replies": [r.to_dict() for r in self.replies],
        }


# ---------------------------------------------------------------------------
# Like  (unique per post + user)
# ---------------------------------------------------------------------------
class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    post = db.relationship("Post", back_populates="likes")
    user = db.relationship("User", back_populates="likes")

    __table_args__ = (db.UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),)


# ---------------------------------------------------------------------------
# Hashtag
# ---------------------------------------------------------------------------
class Hashtag(db.Model):
    __tablename__ = "hashtags"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(100), unique=True, nullable=False, index=True)

    posts = db.relationship("Post", secondary=post_hashtags, back_populates="hashtags")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _relative_time(dt: datetime) -> str:
    """Return a human-readable relative time string."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = int((now - dt).total_seconds())
    if diff < 60:
        return "just now"
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    return f"{diff // 86400}d ago"
