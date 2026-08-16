"""Celery worker entry point.

Start the worker with:

    celery -A celery_worker.celery worker --loglevel=info

On Windows (no fork support) add --pool=solo:

    celery -A celery_worker.celery worker --loglevel=info --pool=solo

How this file works
-------------------
create_app() calls init_extensions(), which:
  - reads CELERY_BROKER_URL / CELERY_RESULT_BACKEND from config
  - calls celery.conf.update() with only the Celery-relevant keys
  - registers ContextTask so every task runs inside a Flask app context

There is nothing extra to do here — we just need the app context to be
created before Celery imports the tasks module.
"""
from app import create_app
from app.extensions import celery  # noqa: F401 — re-exported so Celery CLI can find it

# Build the Flask app.  init_extensions() wires Celery to Redis (or memory://
# in dev) and registers the ContextTask base class.  No further configuration
# is needed in this file.
flask_app = create_app()

# Import tasks *after* create_app() so they are registered on the already-
# configured Celery instance and run inside a Flask app context.
from app.tasks import send_order_confirmation_email  # noqa: F401, E402
