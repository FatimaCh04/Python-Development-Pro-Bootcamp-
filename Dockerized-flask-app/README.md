# DockFlow – Dockerized Flask App with CI/CD Pipeline

## 1. Project Title
DockFlow – Dockerized Flask App with CI/CD Pipeline

## 2. Project Overview
DockFlow is a production-ready Flask backend application designed to demonstrate modern DevOps practices. It provides a clean API foundation wrapped in a secure Docker container, complete with automated testing and a robust Continuous Integration and Continuous Deployment (CI/CD) pipeline powered by GitHub Actions.

## 3. Project Objective
To build a robust, scalable, and automated backend service that serves as a template for modern software engineering workflows. The project aims to showcase how to correctly utilize environment variables, secure containerization, automated testing, and CI/CD pipelines to streamline development and deployment.

## 4. Features
- Clean, modular Flask application factory structure.
- RESTful API endpoints with structured JSON responses.
- Centralized, environment-based configuration.
- Secure Docker configuration running Gunicorn as a non-root user.
- Multi-container orchestration using Docker Compose.
- Comprehensive automated testing using `pytest`.
- Test coverage reporting with `pytest-cov`.
- Automated CI/CD pipeline ensuring code quality and automated Docker Hub publishing.

## 5. Technology Stack
- **Language:** Python 3.12
- **Framework:** Flask
- **WSGI Server:** Gunicorn
- **Testing:** pytest, pytest-cov
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions

## 6. Architecture
```text
Developer
↓
GitHub
↓
GitHub Actions
↓
Tests
↓
Docker Build
↓
Docker Hub
↓
Deployment
```

## 7. Project Structure
```text
dockflow/
├── app/
│   ├── __init__.py      # Flask app factory and error handlers
│   ├── routes.py        # API endpoints
│   └── config.py        # Environment-based configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Pytest session-level env variable setup
│   └── test_routes.py   # Pytest test cases
├── .github/
│   └── workflows/
│       └── ci-cd.yml    # GitHub Actions pipeline
├── Dockerfile           # Docker image configuration
├── docker-compose.yml   # Multi-container orchestration
├── requirements.txt     # Python dependencies
├── run.py               # Application entry point
├── .env.example         # Environment variables template
└── .dockerignore        # Excluded files for Docker builds
```

## 8. Prerequisites
- Python 3.12+
- Docker and Docker Compose
- Git

## 9. Environment Setup
Before running the application, you must configure your environment variables. Copy the provided template to create your `.env` file:
```bash
cp .env.example .env
```
Ensure that `SECRET_KEY`, `APP_NAME`, `APP_VERSION`, and `FLASK_ENV` are populated correctly in the `.env` file.

## 10. Local Flask Setup
Create an isolated Python virtual environment:
```bash
python -m venv .venv
```
*(This command creates a virtual environment folder named `.venv` to keep project dependencies isolated from your system Python).*

Activate the virtual environment (depending on your OS) and install the required dependencies:
```bash
pip install -r requirements.txt
```
*(This command reads the `requirements.txt` file and installs Flask, Gunicorn, pytest, and other necessary libraries into your virtual environment).*

Run the application locally (for development):
```bash
python run.py
```

## 11. Docker Setup
To containerize the application, build the Docker image manually:
```bash
docker build -t dockflow .
```
*(This command reads the `Dockerfile`, downloads the Python 3.12 slim image, installs the requirements, copies the application source code, and tags the resulting image as `dockflow`).*

## 12. Docker Compose Commands
Start the application and its ecosystem in the background:
```bash
docker compose up --build -d
```
*(This command reads `docker-compose.yml`, builds the Docker image if necessary, maps port 5000, loads the `.env` file, and starts the container in detached mode).*

Stop and remove the containers:
```bash
docker compose down
```
*(This command safely shuts down the running containers and cleans up the associated Docker network and resources).*

## 13. API Endpoints
- `GET /` - Root endpoint verifying the API is active.
- `GET /health` - Health check endpoint used by orchestration tools.
- `GET /api/info` - Provides application version and environment metadata.

## 14. Example API Responses
**GET /**
```json
{
    "status": "success",
    "message": "DockFlow API is running"
}
```

**GET /health**
```json
{
    "status": "healthy"
}
```

**GET /api/info**
```json
{
    "application": "DockFlow",
    "version": "1.0.0",
    "environment": "development"
}
```

## 15. Health Check Explanation
The Docker Compose configuration includes an automated health check mechanism. Every 30 seconds, Docker runs `curl -f http://localhost:5000/health` inside the container. This ensures Docker can automatically detect if the Flask application becomes unresponsive and can track the container's health status accurately.

## 16. Testing Commands
Run the automated test suite:
```bash
pytest
```
*(This command automatically discovers and executes all test cases defined in the `tests/` directory to ensure core functionality is intact without regressions).*

## 17. Coverage Command
Generate a test coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```
*(This command runs the tests and calculates what percentage of the `app` directory's codebase is executed during testing, displaying a terminal report that highlights any specific lines of code that lack test coverage).*

## 18. GitHub Actions CI Explanation
The project relies on GitHub Actions for Continuous Integration. On every `push` or `pull_request` to the `main` branch, the CI pipeline automatically:
1. Provisions a fresh Ubuntu environment.
2. Checks out the source code.
3. Sets up Python 3.12 and caches dependencies.
4. Executes the full `pytest` suite along with coverage reporting.
This guarantees that no broken code gets merged into the main repository.

## 19. Docker Image Build Explanation
If the CI tests pass successfully, the pipeline progresses to the build stage. It utilizes Docker Buildx to efficiently construct the Docker image. This crucial step ensures that the application can successfully be containerized without syntax errors, missing dependencies, or configuration faults.

## 20. Docker Hub Publishing Explanation
For Continuous Deployment (CD), direct pushes to the `main` branch trigger an automatic publishing routine. The pipeline securely logs into Docker Hub, tags the freshly built image with both `latest` and the specific Git commit SHA, and pushes it to your public registry. This published Docker image serves as the immutable deployment artifact.

## 21. GitHub Secrets Setup
To enable the CI/CD pipeline to publish images to Docker Hub, you must add the following secrets to your GitHub repository settings (`Settings > Secrets and variables > Actions`):
- `DOCKER_USERNAME`: Your Docker Hub username.
- `DOCKER_PASSWORD`: Your Docker Hub password or Personal Access Token.

*(Optional secrets for VPS deployment: `SERVER_HOST`, `SERVER_USERNAME`, `SERVER_SSH_KEY`)*

## 22. Deployment Explanation
Currently, the pipeline treats publishing the Docker image to Docker Hub as the primary deployment mechanism. Any external server or cloud provider can securely pull the `latest` image from Docker Hub and run it instantly. The workflow also includes conditional logic to gracefully handle optional, direct SSH VPS deployments if configured.

## 23. Troubleshooting
- **Port Conflicts:** If `docker compose up` fails due to port 5000 being in use, modify the port mapping in `docker-compose.yml` (e.g., change `"5000:5000"` to `"8080:5000"`).
- **Environment Errors:** Ensure `.env` is properly created and `SECRET_KEY` is not empty. The application will raise a `ValueError` if the secret key is missing.
- **Python not found (Windows):** If `python` is not recognized, try using the Windows Python Launcher: `py -3 -m venv .venv`.

## 24. Future Improvements
- Implement a relational database layer (e.g., PostgreSQL + SQLAlchemy).
- Add robust user authentication and JWT token management.
- Configure automated deployment directly to a managed cloud container service (e.g., AWS ECS, DigitalOcean App Platform).
- Implement stricter linting and formatting rules (e.g., Flake8, Black) directly into the CI pipeline.

