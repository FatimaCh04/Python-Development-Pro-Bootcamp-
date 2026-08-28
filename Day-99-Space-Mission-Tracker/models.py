from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Mission(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(150),
        nullable=False
    )

    agency = db.Column(
        db.String(100),
        nullable=False
    )

    destination = db.Column(
        db.String(100),
        nullable=False
    )

    launch_date = db.Column(
        db.String(20),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Upcoming"
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    def __repr__(self):
        return f"<Mission {self.name}>"