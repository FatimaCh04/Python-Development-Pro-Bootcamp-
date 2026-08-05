import json
import pytest


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
TASKS_URL = "/tasks"


def _register_and_login(client, username, email, password="Secret123", role="user"):
    client.post(
        REGISTER_URL,
        data=json.dumps({
            "username": username,
            "email": email,
            "password": password,
            "role": role,
        }),
        content_type="application/json",
    )
    res = client.post(
        LOGIN_URL,
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    data = res.get_json()
    return data["data"]["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_task(client, token, payload=None):
    payload = payload or {"title": "Sample task", "priority": "medium"}
    return client.post(
        TASKS_URL,
        data=json.dumps(payload),
        content_type="application/json",
        headers=_auth_headers(token),
    )


# ---------------------------------------------------------------------------
# Create task
# ---------------------------------------------------------------------------

class TestCreateTask:
    def test_create_task_success(self, client):
        token = _register_and_login(client, "creator", "creator@example.com")
        res = _create_task(client, token)
        assert res.status_code == 201
        data = res.get_json()
        assert data["status"] == "success"
        assert data["data"]["title"] == "Sample task"

    def test_create_task_missing_title(self, client):
        token = _register_and_login(client, "notitle", "notitle@example.com")
        res = _create_task(client, token, {"priority": "high"})
        assert res.status_code == 400
        errors = res.get_json().get("errors", {})
        assert "title" in errors

    def test_create_task_invalid_status(self, client):
        token = _register_and_login(client, "badstatus", "badstatus@example.com")
        res = _create_task(client, token, {"title": "Bad", "status": "flying"})
        assert res.status_code == 400

    def test_create_task_invalid_priority(self, client):
        token = _register_and_login(client, "badpriority", "badpriority@example.com")
        res = _create_task(client, token, {"title": "Bad", "priority": "ultra"})
        assert res.status_code == 400

    def test_create_task_unauthenticated(self, client):
        res = client.post(
            TASKS_URL,
            data=json.dumps({"title": "No auth"}),
            content_type="application/json",
        )
        assert res.status_code == 401

    def test_create_task_with_all_fields(self, client):
        token = _register_and_login(client, "fullfields", "fullfields@example.com")
        payload = {
            "title": "Full task",
            "description": "Detailed description",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2030-01-01T00:00:00",
        }
        res = _create_task(client, token, payload)
        assert res.status_code == 201
        d = res.get_json()["data"]
        assert d["status"] == "in_progress"
        assert d["priority"] == "high"
        assert d["description"] == "Detailed description"


# ---------------------------------------------------------------------------
# List tasks
# ---------------------------------------------------------------------------

class TestListTasks:
    def test_list_tasks_empty(self, client):
        token = _register_and_login(client, "listempty", "listempty@example.com")
        res = client.get(TASKS_URL, headers=_auth_headers(token))
        assert res.status_code == 200
        data = res.get_json()
        assert data["data"]["tasks"] == []

    def test_list_tasks_returns_only_own(self, client):
        token_a = _register_and_login(client, "usera", "usera@example.com")
        token_b = _register_and_login(client, "userb", "userb@example.com")
        _create_task(client, token_a, {"title": "Task A"})
        _create_task(client, token_b, {"title": "Task B"})
        res = client.get(TASKS_URL, headers=_auth_headers(token_a))
        tasks = res.get_json()["data"]["tasks"]
        assert all(t["title"] == "Task A" for t in tasks)

    def test_list_tasks_pagination(self, client):
        token = _register_and_login(client, "paginator", "paginator@example.com")
        for i in range(5):
            _create_task(client, token, {"title": f"Task {i}"})
        res = client.get(
            f"{TASKS_URL}?page=1&per_page=2",
            headers=_auth_headers(token),
        )
        assert res.status_code == 200
        data = res.get_json()["data"]
        assert len(data["tasks"]) == 2
        assert data["pagination"]["per_page"] == 2

    def test_list_tasks_filter_by_status(self, client):
        token = _register_and_login(client, "filterstatus", "filterstatus@example.com")
        _create_task(client, token, {"title": "Pending", "status": "pending"})
        _create_task(client, token, {"title": "Done", "status": "completed"})
        res = client.get(
            f"{TASKS_URL}?status=pending",
            headers=_auth_headers(token),
        )
        tasks = res.get_json()["data"]["tasks"]
        assert all(t["status"] == "pending" for t in tasks)

    def test_list_tasks_filter_by_priority(self, client):
        token = _register_and_login(client, "filterprio", "filterprio@example.com")
        _create_task(client, token, {"title": "Low", "priority": "low"})
        _create_task(client, token, {"title": "High", "priority": "high"})
        res = client.get(
            f"{TASKS_URL}?priority=high",
            headers=_auth_headers(token),
        )
        tasks = res.get_json()["data"]["tasks"]
        assert all(t["priority"] == "high" for t in tasks)

    def test_list_tasks_search(self, client):
        token = _register_and_login(client, "searcher", "searcher@example.com")
        _create_task(client, token, {"title": "Buy groceries"})
        _create_task(client, token, {"title": "Pay bills"})
        res = client.get(
            f"{TASKS_URL}?search=groceries",
            headers=_auth_headers(token),
        )
        tasks = res.get_json()["data"]["tasks"]
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Buy groceries"

    def test_list_tasks_sort_oldest(self, client):
        token = _register_and_login(client, "sorter", "sorter@example.com")
        _create_task(client, token, {"title": "First"})
        _create_task(client, token, {"title": "Second"})
        res = client.get(
            f"{TASKS_URL}?sort=oldest",
            headers=_auth_headers(token),
        )
        tasks = res.get_json()["data"]["tasks"]
        assert tasks[0]["title"] == "First"


# ---------------------------------------------------------------------------
# Get single task
# ---------------------------------------------------------------------------

class TestGetTask:
    def test_get_task_success(self, client):
        token = _register_and_login(client, "getter", "getter@example.com")
        created = _create_task(client, token, {"title": "Get me"})
        task_id = created.get_json()["data"]["id"]
        res = client.get(
            f"{TASKS_URL}/{task_id}",
            headers=_auth_headers(token),
        )
        assert res.status_code == 200
        assert res.get_json()["data"]["title"] == "Get me"

    def test_get_task_not_found(self, client):
        token = _register_and_login(client, "getnotfound", "getnotfound@example.com")
        res = client.get(f"{TASKS_URL}/99999", headers=_auth_headers(token))
        assert res.status_code == 404

    def test_get_task_forbidden(self, client):
        token_a = _register_and_login(client, "ownerget", "ownerget@example.com")
        token_b = _register_and_login(client, "thiefget", "thiefget@example.com")
        created = _create_task(client, token_a, {"title": "Private"})
        task_id = created.get_json()["data"]["id"]
        res = client.get(
            f"{TASKS_URL}/{task_id}",
            headers=_auth_headers(token_b),
        )
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# Update task
# ---------------------------------------------------------------------------

class TestUpdateTask:
    def test_update_task_success(self, client):
        token = _register_and_login(client, "updater", "updater@example.com")
        created = _create_task(client, token, {"title": "Old title"})
        task_id = created.get_json()["data"]["id"]
        res = client.put(
            f"{TASKS_URL}/{task_id}",
            data=json.dumps({"title": "New title", "status": "in_progress"}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert res.status_code == 200
        d = res.get_json()["data"]
        assert d["title"] == "New title"
        assert d["status"] == "in_progress"

    def test_update_task_not_found(self, client):
        token = _register_and_login(client, "updatenf", "updatenf@example.com")
        res = client.put(
            f"{TASKS_URL}/99999",
            data=json.dumps({"title": "Ghost"}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert res.status_code == 404

    def test_update_task_forbidden(self, client):
        token_a = _register_and_login(client, "ownrupdate", "ownrupdate@example.com")
        token_b = _register_and_login(client, "thiefupdate", "thiefupdate@example.com")
        created = _create_task(client, token_a, {"title": "Locked"})
        task_id = created.get_json()["data"]["id"]
        res = client.put(
            f"{TASKS_URL}/{task_id}",
            data=json.dumps({"title": "Stolen"}),
            content_type="application/json",
            headers=_auth_headers(token_b),
        )
        assert res.status_code == 403

    def test_update_task_invalid_status(self, client):
        token = _register_and_login(client, "updbadinput", "updbadinput@example.com")
        created = _create_task(client, token, {"title": "Check status"})
        task_id = created.get_json()["data"]["id"]
        res = client.put(
            f"{TASKS_URL}/{task_id}",
            data=json.dumps({"status": "invalid_status"}),
            content_type="application/json",
            headers=_auth_headers(token),
        )
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# Delete task
# ---------------------------------------------------------------------------

class TestDeleteTask:
    def test_delete_task_success(self, client):
        token = _register_and_login(client, "deleter", "deleter@example.com")
        created = _create_task(client, token, {"title": "Delete me"})
        task_id = created.get_json()["data"]["id"]
        res = client.delete(
            f"{TASKS_URL}/{task_id}",
            headers=_auth_headers(token),
        )
        assert res.status_code == 200
        # Confirm it's gone
        res2 = client.get(
            f"{TASKS_URL}/{task_id}",
            headers=_auth_headers(token),
        )
        assert res2.status_code == 404

    def test_delete_task_not_found(self, client):
        token = _register_and_login(client, "deletenf", "deletenf@example.com")
        res = client.delete(f"{TASKS_URL}/99999", headers=_auth_headers(token))
        assert res.status_code == 404

    def test_delete_task_forbidden(self, client):
        token_a = _register_and_login(client, "ownrdelete", "ownrdelete@example.com")
        token_b = _register_and_login(client, "thiefdelete", "thiefdelete@example.com")
        created = _create_task(client, token_a, {"title": "Mine"})
        task_id = created.get_json()["data"]["id"]
        res = client.delete(
            f"{TASKS_URL}/{task_id}",
            headers=_auth_headers(token_b),
        )
        assert res.status_code == 403

    def test_delete_task_unauthenticated(self, client):
        res = client.delete(f"{TASKS_URL}/1")
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# Admin tests
# ---------------------------------------------------------------------------

class TestAdminEndpoints:
    def test_admin_list_users(self, client):
        admin_token = _register_and_login(
            client, "adminlst", "adminlst@example.com", "Admin123", "admin"
        )
        res = client.get("/admin/users", headers=_auth_headers(admin_token))
        assert res.status_code == 200
        assert "users" in res.get_json()["data"]

    def test_admin_list_users_forbidden_for_user(self, client):
        token = _register_and_login(
            client, "plainuser2", "plainuser2@example.com"
        )
        res = client.get("/admin/users", headers=_auth_headers(token))
        assert res.status_code == 403

    def test_admin_list_all_tasks(self, client):
        admin_token = _register_and_login(
            client, "adminalltsks", "adminalltsks@example.com", "Admin123", "admin"
        )
        res = client.get("/admin/tasks", headers=_auth_headers(admin_token))
        assert res.status_code == 200

    def test_admin_delete_any_task(self, client):
        user_token = _register_and_login(
            client, "taskowner2", "taskowner2@example.com"
        )
        admin_token = _register_and_login(
            client, "admindelete", "admindelete@example.com", "Admin123", "admin"
        )
        created = _create_task(client, user_token, {"title": "Admin will delete"})
        task_id = created.get_json()["data"]["id"]
        res = client.delete(
            f"/admin/tasks/{task_id}",
            headers=_auth_headers(admin_token),
        )
        assert res.status_code == 200
