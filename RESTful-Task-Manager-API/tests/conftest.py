import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    _app = create_app("testing")
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test function."""
    with app.app_context():
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()


@pytest.fixture(scope="function")
def client(app):
    """Return a test client."""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Return a test CLI runner."""
    return app.test_cli_runner()
