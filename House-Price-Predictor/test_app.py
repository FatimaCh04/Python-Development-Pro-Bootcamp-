"""
test_app.py
Pytest suite for the HousePrice AI Flask application.
Run: py -m pytest test_app.py -v
"""
import json
import pytest
from app import app as flask_app, pipeline


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


VALID_PAYLOAD = {
    'area_sqft': 2500,
    'bedrooms':  4,
    'bathrooms': 3,
    'location':  'DHA',
}


# ── 1. Homepage ────────────────────────────────────────────────────────────────
def test_homepage_returns_200(client):
    r = client.get('/')
    assert r.status_code == 200
    assert b'HousePrice AI' in r.data


# ── 2. Model loading ───────────────────────────────────────────────────────────
def test_pipeline_is_loaded():
    assert pipeline is not None, 'Pipeline failed to load — run train_model.py first.'
    assert hasattr(pipeline, 'predict')


# ── 3. Valid prediction ────────────────────────────────────────────────────────
def test_valid_prediction_returns_200(client):
    r = client.post('/predict',
                    data=json.dumps(VALID_PAYLOAD),
                    content_type='application/json')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['success'] is True
    assert 'predicted_price' in data
    assert data['currency'] == 'PKR'


# ── 4. Output type ─────────────────────────────────────────────────────────────
def test_predicted_price_is_numeric(client):
    r = client.post('/predict',
                    data=json.dumps(VALID_PAYLOAD),
                    content_type='application/json')
    data = json.loads(r.data)
    assert isinstance(data['predicted_price'], (int, float))


# ── 5. Prediction is positive ──────────────────────────────────────────────────
def test_predicted_price_is_positive(client):
    r = client.post('/predict',
                    data=json.dumps(VALID_PAYLOAD),
                    content_type='application/json')
    data = json.loads(r.data)
    assert data['predicted_price'] > 0


# ── 6. Missing fields ──────────────────────────────────────────────────────────
def test_missing_area_returns_400(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'area_sqft'}
    r = client.post('/predict', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 400
    assert json.loads(r.data)['success'] is False


def test_missing_location_returns_400(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != 'location'}
    r = client.post('/predict', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 400


# ── 7. Invalid area ────────────────────────────────────────────────────────────
def test_negative_area_returns_400(client):
    r = client.post('/predict',
                    data=json.dumps({**VALID_PAYLOAD, 'area_sqft': -500}),
                    content_type='application/json')
    assert r.status_code == 400
    assert json.loads(r.data)['success'] is False


def test_zero_area_returns_400(client):
    r = client.post('/predict',
                    data=json.dumps({**VALID_PAYLOAD, 'area_sqft': 0}),
                    content_type='application/json')
    assert r.status_code == 400


# ── 8. Invalid bedrooms ────────────────────────────────────────────────────────
def test_zero_bedrooms_returns_400(client):
    r = client.post('/predict',
                    data=json.dumps({**VALID_PAYLOAD, 'bedrooms': 0}),
                    content_type='application/json')
    assert r.status_code == 400


def test_negative_bedrooms_returns_400(client):
    r = client.post('/predict',
                    data=json.dumps({**VALID_PAYLOAD, 'bedrooms': -3}),
                    content_type='application/json')
    assert r.status_code == 400


# ── 9. Invalid bathrooms ───────────────────────────────────────────────────────
def test_zero_bathrooms_returns_400(client):
    r = client.post('/predict',
                    data=json.dumps({**VALID_PAYLOAD, 'bathrooms': 0}),
                    content_type='application/json')
    assert r.status_code == 400


# ── 10. Invalid location ───────────────────────────────────────────────────────
def test_unknown_location_returns_400(client):
    r = client.post('/predict',
                    data=json.dumps({**VALID_PAYLOAD, 'location': 'Atlantis'}),
                    content_type='application/json')
    assert r.status_code == 400
    data = json.loads(r.data)
    assert data['success'] is False


# ── 11. Different inputs produce different predictions ─────────────────────────
def test_different_inputs_give_different_predictions(client):
    p1 = {**VALID_PAYLOAD, 'area_sqft': 1000, 'location': 'North Nazimabad'}
    p2 = {**VALID_PAYLOAD, 'area_sqft': 5000, 'location': 'Clifton'}

    r1 = client.post('/predict', data=json.dumps(p1), content_type='application/json')
    r2 = client.post('/predict', data=json.dumps(p2), content_type='application/json')

    price1 = json.loads(r1.data)['predicted_price']
    price2 = json.loads(r2.data)['predicted_price']

    assert price1 != price2, 'Two very different inputs should not give identical predictions'
    assert price2 > price1,  'Larger DHA property should cost more than smaller North Nazimabad'


# ── 12. Non-JSON content type ──────────────────────────────────────────────────
def test_non_json_request_returns_415(client):
    r = client.post('/predict',
                    data='area=2000&bedrooms=3&bathrooms=2&location=DHA',
                    content_type='application/x-www-form-urlencoded')
    assert r.status_code == 415
