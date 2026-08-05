import json
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"

USER_PAYLOAD = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "Secret123",
    "role": "user",
}

ADMIN_PAYLOAD = {
    "username": "adminuser",
    "email": "admin@example.com",
    "password": "Admin123",
    "role": "admin",
}


def register_user(client, payload=None):
    payload = payload or USER_PAYLOAD
    return client.post(
        REGISTER_URL,
        data=json.dumps(payload),
        content_type="application/json",
    )


def login_user(client, email=None, password=None):
    email = email or USER_PAYLOAD["email"]
    password = password or USER_PAYLOAD["password"]
    return client.post(
        LOGIN_URL,
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_success(self, client):
        res = register_user(client)
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"
        assert data["data"]["email"] == USER_PAYLOAD["email"]
        assert data["data"]["username"] == USER_PAYLOAD["username"]
        assert "password_hash" not in data["data"]

    def test_register_duplicate_email(self, client):
        register_user(client)
        res = register_user(client)
        assert res.status_code == 400
        data = res.get_json()
        assert data["status"] == "error"

    def test_register_duplicate_username(self, client):
        register_user(client)
        payload = USER_PAYLOAD.copy()
        payload["email"] = "different@example.com"
        res = register_user(client, payload)
        assert res.status_code == 400

    def test_register_missing_email(self, client):
        payload = {"username": "nomail", "password": "Secret123"}
        res = client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert res.status_code == 400
        data = res.get_json()
        assert "email" in data.get("errors", {})

    def test_register_invalid_email(self, client):
        payload = {
            "username": "bademail",
            "email": "not-an-email",
            "password": "Secret123",
        }
        res = client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_register_weak_password(self, client):
        payload = {
            "username": "weakpass",
            "email": "weak@example.com",
            "password": "short",
        }
        res = client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_register_password_no_uppercase(self, client):
        payload = {
            "username": "noupper",
            "email": "noupper@example.com",
            "password": "alllower1",
        }
        res = client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_register_password_no_digit(self, client):
        payload = {
            "username": "nodigit",
            "email": "nodigit@example.com",
            "password": "AllLettersNone",
        }
        res = client.post(
            REGISTER_URL,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_register_no_body(self, client):
        res = client.post(REGISTER_URL, content_type="application/json")
        assert res.status_code == 400

    def test_register_admin_role(self, client):
        res = register_user(client, ADMIN_PAYLOAD)
        assert res.status_code == 201
        data = res.get_json()
        assert data["data"]["role"] == "admin"


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client):
        register_user(client)
        res = login_user(client)
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert "user" in data["data"]

    def test_login_wrong_password(self, client):
        register_user(client)
        res = login_user(client, password="WrongPass999")
        assert res.status_code == 401

    def test_login_unknown_email(self, client):
        res = login_user(client, email="nobody@example.com", password="Secret123")
        assert res.status_code == 401

    def test_login_missing_password(self, client):
        register_user(client)
        res = client.post(
            LOGIN_URL,
            data=json.dumps({"email": USER_PAYLOAD["email"]}),
            content_type="application/json",
        )
        assert res.status_code == 400

    def test_login_no_body(self, client):
        res = client.post(LOGIN_URL, content_type="application/json")
        assert res.status_code == 400

    def test_login_returns_jwt(self, client):
        register_user(client)
        res = login_user(client)
        token = res.get_json()["data"]["access_token"]
        # A JWT has three dot-separated base64url parts
        assert token.count(".") == 2

    def test_login_invalid_email_format(self, client):
        res = client.post(
            LOGIN_URL,
            data=json.dumps({"email": "bademail", "password": "Secret123"}),
            content_type="application/json",
        )
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# JWT / protected route tests
# ---------------------------------------------------------------------------

class TestJWT:
    def test_protected_without_token(self, client):
        res = client.get("/tasks")
        assert res.status_code == 401

    def test_protected_with_invalid_token(self, client):
        res = client.get(
            "/tasks",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert res.status_code == 422 or res.status_code == 401

    def test_protected_with_valid_token(self, client):
        register_user(client)
        login_res = login_user(client)
        token = login_res.get_json()["data"]["access_token"]
        res = client.get(
            "/tasks",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
