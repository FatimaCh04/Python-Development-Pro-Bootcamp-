from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pathlib import Path


app = Flask(__name__)

# Database configuration
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{INSTANCE_DIR / 'todo.db'}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# DATABASE MODEL
# ============================================================

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# Create database
with app.app_context():
    db.create_all()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    todos = Todo.query.order_by(
        Todo.created_at.desc()
    ).all()

    total_tasks = len(todos)

    completed_tasks = Todo.query.filter_by(
        completed=True
    ).count()

    pending_tasks = Todo.query.filter_by(
        completed=False
    ).count()

    return render_template(
        "index.html",
        todos=todos,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )


# ============================================================
# ADD TASK
# ============================================================

@app.route("/add", methods=["GET", "POST"])
def add_task():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title:

            return render_template(
                "add.html",
                error="Task title is required."
            )

        todo = Todo(
            title=title,
            description=description
        )

        db.session.add(todo)
        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template("add.html")


# ============================================================
# EDIT TASK
# ============================================================

@app.route(
    "/edit/<int:task_id>",
    methods=["GET", "POST"]
)
def edit_task(task_id):

    todo = db.get_or_404(
        Todo,
        task_id
    )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not title:

            return render_template(
                "edit.html",
                todo=todo,
                error="Task title is required."
            )

        todo.title = title
        todo.description = description

        db.session.commit()

        return redirect(
            url_for("home")
        )

    return render_template(
        "edit.html",
        todo=todo
    )


# ============================================================
# COMPLETE / UNCOMPLETE TASK
# ============================================================

@app.route(
    "/complete/<int:task_id>",
    methods=["POST"]
)
def toggle_task(task_id):

    todo = db.get_or_404(
        Todo,
        task_id
    )

    todo.completed = not todo.completed

    db.session.commit()

    return redirect(
        url_for("home")
    )


# ============================================================
# DELETE TASK
# ============================================================

@app.route(
    "/delete/<int:task_id>",
    methods=["POST"]
)
def delete_task(task_id):

    todo = db.get_or_404(
        Todo,
        task_id
    )

    db.session.delete(todo)
    db.session.commit()

    return redirect(
        url_for("home")
    )


# ============================================================
# CLEAR COMPLETED TASKS
# ============================================================

@app.route(
    "/clear-completed",
    methods=["POST"]
)
def clear_completed():

    Todo.query.filter_by(
        completed=True
    ).delete()

    db.session.commit()

    return redirect(
        url_for("home")
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )