from app import app
from models import db, Mission


sample_missions = [
    {
        "name": "Artemis II",
        "agency": "NASA",
        "destination": "Moon",
        "launch_date": "2026-04-01",
        "status": "Completed",
        "description": (
            "A crewed lunar mission designed to test "
            "systems required for future lunar exploration."
        )
    },
    {
        "name": "Europa Clipper",
        "agency": "NASA",
        "destination": "Europa",
        "launch_date": "2024-10-14",
        "status": "Active",
        "description": (
            "A scientific mission studying Jupiter's moon "
            "Europa and investigating its potential habitability."
        )
    },
    {
        "name": "Mars Sample Return",
        "agency": "NASA / ESA",
        "destination": "Mars",
        "launch_date": "2028-08-15",
        "status": "Upcoming",
        "description": (
            "A planned campaign designed to return "
            "carefully selected Martian samples to Earth."
        )
    },
    {
        "name": "JUICE",
        "agency": "ESA",
        "destination": "Jupiter",
        "launch_date": "2023-04-14",
        "status": "Active",
        "description": (
            "The Jupiter Icy Moons Explorer mission "
            "will study Jupiter and its icy moons."
        )
    },
    {
        "name": "Psyche",
        "agency": "NASA",
        "destination": "Asteroid Psyche",
        "launch_date": "2023-10-13",
        "status": "Active",
        "description": (
            "A mission exploring the metal-rich asteroid "
            "16 Psyche to better understand planetary cores."
        )
    },
    {
        "name": "Europa Lander",
        "agency": "Space Research",
        "destination": "Europa",
        "launch_date": "2030-06-10",
        "status": "Upcoming",
        "description": (
            "A conceptual future mission focused on "
            "surface investigation of Europa."
        )
    }
]


with app.app_context():

    db.create_all()

    if Mission.query.count() == 0:

        for data in sample_missions:
            mission = Mission(**data)
            db.session.add(mission)

        db.session.commit()

        print("Sample missions added successfully.")

    else:
        print("Database already contains missions.")