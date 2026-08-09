import pytest
import os

# Set required environment variables before importing app to prevent ValueError during collection
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['APP_NAME'] = 'DockFlow'
os.environ['APP_VERSION'] = '1.0.0'
os.environ['FLASK_ENV'] = 'testing'

from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "message": "DockFlow API is running"
    }

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy"
    }

def test_info(client):
    response = client.get('/api/info')
    assert response.status_code == 200
    data = response.get_json()
    assert data['application'] == 'DockFlow'
    assert data['version'] == '1.0.0'
    assert data['environment'] == 'testing'

def test_404(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not Found", "status_code": 404}

def test_405(client):
    response = client.post('/')
    assert response.status_code == 405
    assert response.get_json() == {"error": "Method Not Allowed", "status_code": 405}
