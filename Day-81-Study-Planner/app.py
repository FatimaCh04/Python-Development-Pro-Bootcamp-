from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///study_planner.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Study Task Model
class StudyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    notes = db.Column(db.Text, nullable=True)


# Create database
with app.app_context():
    db.create_all()


# Home / Dashboard
@app.route("/")
def index():

    search = request.args.get("search", "")
    priority_filter = request.args.get("priority", "")
    status_filter = request.args.get("status", "")

    query = StudyTask.query

    # Search
    if search:
        query = query.filter(
            db.or_(
                StudyTask.title.ilike(f"%{search}%"),
                StudyTask.subject.ilike(f"%{search}%")
            )
        )

    # Priority filter
    if priority_filter:
        query = query.filter(
            StudyTask.priority == priority_filter
        )

    # Status filter
    if status_filter:
        query = query.filter(
            StudyTask.status == status_filter
        )

    tasks = query.order_by(
        StudyTask.id.desc()
    ).all()

    # Statistics
    total = StudyTask.query.count()

    pending = StudyTask.query.filter_by(
        status="Pending"
    ).count()

    completed = StudyTask.query.filter_by(
        status="Completed"
    ).count()

    high_priority = StudyTask.query.filter_by(
        priority="High"
    ).count()

    return render_template(
        "index.html",
        tasks=tasks,
        search=search,
        priority_filter=priority_filter,
        status_filter=status_filter,
        total=total,
        pending=pending,
        completed=completed,
        high_priority=high_priority
    )


# Add Task
@app.route("/add", methods=["GET", "POST"])
def add_task():

    if request.method == "POST":

        title = request.form["title"]
        subject = request.form["subject"]
        deadline = request.form["deadline"]
        priority = request.form["priority"]
        notes = request.form["notes"]

        new_task = StudyTask(
            title=title,
            subject=subject,
            deadline=deadline,
            priority=priority,
            status="Pending",
            notes=notes
        )

        db.session.add(new_task)
        db.session.commit()

        return redirect(url_for("index"))

    today = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "add.html",
        today=today
    )


# Edit Task
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_task(id):

    task = StudyTask.query.get_or_404(id)

    if request.method == "POST":

        task.title = request.form["title"]
        task.subject = request.form["subject"]
        task.deadline = request.form["deadline"]
        task.priority = request.form["priority"]
        task.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        task=task
    )


# Delete Task
@app.route("/delete/<int:id>")
def delete_task(id):

    task = StudyTask.query.get_or_404(id)

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("index"))


# Mark Task as Completed
@app.route("/complete/<int:id>")
def complete_task(id):

    task = StudyTask.query.get_or_404(id)

    if task.status == "Pending":
        task.status = "Completed"
    else:
        task.status = "Pending"

    db.session.commit()

    return redirect(url_for("index"))


# Clear Completed Tasks
@app.route("/clear-completed")
def clear_completed():

    StudyTask.query.filter_by(
        status="Completed"
    ).delete()

    db.session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)