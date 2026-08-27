from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Job Application Model
class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    company = db.Column(db.String(100), nullable=False)

    position = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    status = db.Column(db.String(50), nullable=False)

    application_date = db.Column(db.String(20), nullable=False)

    notes = db.Column(db.Text, nullable=True)


# Create database
with app.app_context():
    db.create_all()


# Home page
@app.route("/")
def index():

    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    query = JobApplication.query

    # Search
    if search:
        query = query.filter(
            db.or_(
                JobApplication.company.ilike(f"%{search}%"),
                JobApplication.position.ilike(f"%{search}%"),
                JobApplication.location.ilike(f"%{search}%")
            )
        )

    # Status filter
    if status_filter:
        query = query.filter(
            JobApplication.status == status_filter
        )

    jobs = query.order_by(
        JobApplication.id.desc()
    ).all()

    # Statistics
    total = JobApplication.query.count()

    applied = JobApplication.query.filter_by(
        status="Applied"
    ).count()

    interview = JobApplication.query.filter_by(
        status="Interview"
    ).count()

    selected = JobApplication.query.filter_by(
        status="Selected"
    ).count()

    rejected = JobApplication.query.filter_by(
        status="Rejected"
    ).count()

    return render_template(
        "index.html",
        jobs=jobs,
        search=search,
        status_filter=status_filter,
        total=total,
        applied=applied,
        interview=interview,
        selected=selected,
        rejected=rejected
    )


# Add application
@app.route("/add", methods=["GET", "POST"])
def add_job():

    if request.method == "POST":

        company = request.form["company"]
        position = request.form["position"]
        location = request.form["location"]
        status = request.form["status"]
        application_date = request.form["application_date"]
        notes = request.form["notes"]

        new_job = JobApplication(
            company=company,
            position=position,
            location=location,
            status=status,
            application_date=application_date,
            notes=notes
        )

        db.session.add(new_job)
        db.session.commit()

        return redirect(url_for("index"))

    # Default date
    today = datetime.now().strftime("%Y-%m-%d")

    return render_template(
        "add.html",
        today=today
    )


# Edit application
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_job(id):

    job = JobApplication.query.get_or_404(id)

    if request.method == "POST":

        job.company = request.form["company"]
        job.position = request.form["position"]
        job.location = request.form["location"]
        job.status = request.form["status"]
        job.application_date = request.form["application_date"]
        job.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        job=job
    )


# Delete application
@app.route("/delete/<int:id>")
def delete_job(id):

    job = JobApplication.query.get_or_404(id)

    db.session.delete(job)
    db.session.commit()

    return redirect(url_for("index"))


# Update status quickly
@app.route("/status/<int:id>/<new_status>")
def update_status(id, new_status):

    job = JobApplication.query.get_or_404(id)

    allowed_statuses = [
        "Applied",
        "Interview",
        "Selected",
        "Rejected"
    ]

    if new_status in allowed_statuses:

        job.status = new_status

        db.session.commit()

    return redirect(url_for("index"))


# Run application
if __name__ == "__main__":
    app.run(debug=True)