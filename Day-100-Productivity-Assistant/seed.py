from app import app
from models import db, Task


sample_tasks = [
    {
        "title": "Complete Python Day 100",
        "description": "Finish the final project and publish it on GitHub.",
        "priority": "High",
        "due_date": "2026-08-30",
        "category": "Learning",
        "completed": False
    },
    {
        "title": "Review Flask Concepts",
        "description": "Review routes, templates, forms and SQLAlchemy.",
        "priority": "Medium",
        "due_date": "2026-09-01",
        "category": "Learning",
        "completed": False
    },
    {
        "title": "Update GitHub Profile",
        "description": "Add recent Python projects to the profile.",
        "priority": "Low",
        "due_date": "2026-09-03",
        "category": "Career",
        "completed": False
    },
    {
        "title": "Build Project Documentation",
        "description": "Write professional documentation for completed projects.",
        "priority": "Medium",
        "due_date": "2026-09-05",
        "category": "Career",
        "completed": True
    },
]


with app.app_context():
    db.create_all()

    if Task.query.count() == 0:
        for data in sample_tasks:
            db.session.add(Task(**data))

        db.session.commit()

        print("Sample tasks added successfully.")
    else:
        print("Database already contains tasks.")