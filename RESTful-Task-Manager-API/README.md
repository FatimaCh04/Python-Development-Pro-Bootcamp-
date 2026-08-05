# RESTful Task Manager API

A production-ready RESTful API for managing tasks, built with **Flask**, **Flask-JWT-Extended**, **SQLAlchemy**, **Marshmallow**, and **PostgreSQL**.

---

## Features

- **JWT Authentication** – Register, login, and protect routes with Bearer tokens
- **Role-Based Access Control** – `admin` and `user` roles with distinct permissions
- **Full Task CRUD** – Create, list, retrieve, update, delete tasks
- **Filtering** – Filter by `status` and `priority`
- **Search** – Full-text search across `title` and `description`
- **Pagination** – `?page` and `?per_page` query parameters
- **Sorting** – Sort by `newest`, `oldest`, or `due_date`
- **Marshmallow Validation** – Strict input validation on every endpoint
- **Rate Limiting** – 100 requests/hour per IP (Flask-Limiter)
- **Swagger UI** – Interactive API docs at `/apidocs`
- **Postman Collection** – Ready-to-import collection in `docs/`
- **Pytest Suite** – 40+ tests covering auth, CRUD, permissions, edge cases

---

## Folder Structure

```
RESTful-Task-Manager-API/
├── app/
│   ├── __init__.py        # App factory
│   ├── config.py          # Dev / Prod / Test configuration
│   ├── extensions.py      # Flask extension singletons
│   ├── models.py          # SQLAlchemy User & Task models
│   ├── schemas.py         # Marshmallow validation schemas
│   ├── auth.py            # /auth/register and /auth/login
│   ├── resources.py       # /tasks and /admin blueprints
│   ├── decorators.py      # @admin_required, @jwt_required_with_identity
│   └── utils.py           # success_response, error_response, paginate_query
├── migrations/            # Flask-Migrate generated migrations
├── tests/
│   ├── conftest.py        # Pytest fixtures
│   ├── test_auth.py       # Register / Login / JWT tests
│   └── test_tasks.py      # Task CRUD / admin tests
├── docs/
│   └── postman_collection.json
├── instance/              # SQLite instance (testing only)
├── run.py                 # Application entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.13+ |
| PostgreSQL | 14+ |
| pip | latest |

---

## Database Setup

### 1. Create the PostgreSQL database

```sql
CREATE DATABASE task_manager_db;
```

### 2. Initialise Flask-Migrate

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## Running the Project

```bash
# Development server
flask run

# Or using run.py directly
python run.py
```

The API will be available at **http://localhost:5000**.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Entry point | `run.py` |
| `FLASK_ENV` | `development` / `production` / `testing` | `development` |
| `SECRET_KEY` | Flask secret key | — |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `JWT_SECRET_KEY` | JWT signing secret | — |
| `JWT_ACCESS_TOKEN_EXPIRES` | Token TTL in seconds | `3600` |
| `RATELIMIT_STORAGE_URL` | Rate limit backend (`memory://` or Redis URL) | `memory://` |

---

## API Endpoints

### Health

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/health` | API health check |

### Authentication

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Log in and receive JWT | No |

### Tasks

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| POST | `/tasks` | Create a task | JWT |
| GET | `/tasks` | List own tasks (filter/sort/paginate) | JWT |
| GET | `/tasks/<id>` | Get a task by ID | JWT |
| PUT | `/tasks/<id>` | Update a task | JWT |
| DELETE | `/tasks/<id>` | Delete a task | JWT |

### Admin

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/admin/users` | List all users | Admin JWT |
| GET | `/admin/tasks` | List all tasks | Admin JWT |
| DELETE | `/admin/tasks/<id>` | Delete any task | Admin JWT |

---

## Authentication

All protected routes require the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

### Register

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"johndoe","email":"john@example.com","password":"Secret123","role":"user"}'
```

### Login

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"Secret123"}'
```

The response contains `access_token`. Use it in subsequent requests.

---

## Query Parameters

### Filtering

| Parameter | Values | Example |
|-----------|--------|---------|
| `status` | `pending`, `in_progress`, `completed`, `cancelled` | `?status=pending` |
| `priority` | `low`, `medium`, `high`, `critical` | `?priority=high` |
| `search` | Any string | `?search=groceries` |

### Sorting

| Parameter | Values |
|-----------|--------|
| `sort` | `newest` (default), `oldest`, `due_date` |

### Pagination

| Parameter | Default | Max |
|-----------|---------|-----|
| `page` | `1` | — |
| `per_page` | `10` | `100` |

---

## Swagger UI

Swagger interactive documentation is available at:

```
http://localhost:5000/apidocs
```

All endpoints are documented with request/response schemas. To test protected endpoints, use the **Authorize** button and enter:

```
Bearer <your_access_token>
```

---

## Postman Collection

Import `docs/postman_collection.json` into Postman.

1. Open Postman → **Import** → select `docs/postman_collection.json`
2. Set the `base_url` collection variable to `http://localhost:5000`
3. Run **Login** – the `access_token` variable is set automatically
4. Use any other request with `{{access_token}}` pre-filled

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_auth.py -v
pytest tests/test_tasks.py -v

# Run with coverage report
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

The test suite uses SQLite in-memory so **no PostgreSQL** is required for testing.

---

## User Roles

### User (`role: "user"`)
- Create tasks
- View, update, and delete **own tasks only**

### Admin (`role: "admin"`)
- All user permissions
- View **all users** via `/admin/users`
- View **all tasks** via `/admin/tasks`
- Delete **any task** via `/admin/tasks/<id>`

---

## Validation Rules

| Field | Rules |
|-------|-------|
| `username` | 3–80 chars, alphanumeric + underscores |
| `email` | Valid RFC email format |
| `password` | Min 8 chars, ≥1 uppercase letter, ≥1 digit |
| `title` | 1–200 chars |
| `status` | One of `pending`, `in_progress`, `completed`, `cancelled` |
| `priority` | One of `low`, `medium`, `high`, `critical` |
| `due_date` | ISO 8601 datetime string |

---

## Rate Limiting

- **Default**: 100 requests per hour per IP address
- **Register**: 10 requests per hour per IP
- **Login**: 20 requests per hour per IP

HTTP `429 Too Many Requests` is returned when limits are exceeded.

---

## Error Responses

All errors return a consistent JSON structure:

```json
{
  "status": "error",
  "message": "Human readable message.",
  "status_code": 400,
  "errors": {
    "field": ["validation detail"]
  }
}
```

| Code | Meaning |
|------|---------|
| 400 | Bad Request / Validation Error |
| 401 | Unauthorised (missing or invalid JWT) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource Not Found |
| 405 | Method Not Allowed |
| 422 | Unprocessable Entity (malformed JWT) |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

