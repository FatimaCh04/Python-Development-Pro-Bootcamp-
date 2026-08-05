import enum
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tasks = db.relationship(
        "Task",
        backref="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        """Return True if this user has the admin role."""
        return self.role == UserRole.ADMIN

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} role={self.role.value!r}>"


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(TaskStatus, name="task_status_enum"),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    priority = db.Column(
        db.Enum(TaskPriority, name="task_priority_enum"),
        nullable=False,
        default=TaskPriority.MEDIUM,
    )
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
        }

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status.value!r}>"
