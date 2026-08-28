from flask import Flask, render_template, request, redirect, url_for
from models import db, Mission

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///missions.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


with app.app_context():
    db.create_all()


@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "All")

    query = Mission.query

    if search:
        query = query.filter(
            db.or_(
                Mission.name.ilike(f"%{search}%"),
                Mission.agency.ilike(f"%{search}%"),
                Mission.destination.ilike(f"%{search}%")
            )
        )

    if status != "All":
        query = query.filter_by(status=status)

    missions = query.order_by(Mission.launch_date.desc()).all()

    total = Mission.query.count()
    successful = Mission.query.filter_by(status="Completed").count()
    upcoming = Mission.query.filter_by(status="Upcoming").count()
    active = Mission.query.filter_by(status="Active").count()

    return render_template(
        "index.html",
        missions=missions,
        search=search,
        selected_status=status,
        total=total,
        successful=successful,
        upcoming=upcoming,
        active=active
    )


@app.route("/mission/<int:mission_id>")
def mission_details(mission_id):
    mission = Mission.query.get_or_404(mission_id)
    return render_template("mission.html", mission=mission)


@app.route("/add", methods=["POST"])
def add_mission():

    name = request.form.get("name", "").strip()
    agency = request.form.get("agency", "").strip()
    destination = request.form.get("destination", "").strip()
    launch_date = request.form.get("launch_date", "").strip()
    status = request.form.get("status", "Upcoming")
    description = request.form.get("description", "").strip()

    if name and agency and destination and launch_date:

        mission = Mission(
            name=name,
            agency=agency,
            destination=destination,
            launch_date=launch_date,
            status=status,
            description=description
        )

        db.session.add(mission)
        db.session.commit()

    return redirect(url_for("index"))


@app.route("/delete/<int:mission_id>", methods=["POST"])
def delete_mission(mission_id):

    mission = Mission.query.get_or_404(mission_id)

    db.session.delete(mission)
    db.session.commit()

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)