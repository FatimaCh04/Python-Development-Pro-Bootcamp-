# Python 3.12 slim — latest stable that all pinned packages support cleanly.
# NOTE: local dev may run a different Python version (e.g. 3.14); the container
# is intentionally pinned to 3.12 for reproducibility.
FROM python:3.12-slim

WORKDIR /app

# Build-time env — keep .pyc files out of the image and ensure stdout/stderr
# are unbuffered so container logs appear immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies
#   gcc          — needed to compile some Python C extensions
#   libpq-dev    — header files required by psycopg2 (psycopg2-binary bundles
#                  its own libpq, but having the client tools available makes
#                  debugging easier)
#   postgresql-client — gives us psql for health-check scripts
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create the non-root user BEFORE copying application code so that the COPY
# --chown flag below sets ownership in a single layer (no extra chown -R pass).
RUN useradd -m -u 1000 appuser

# Install Python dependencies as root (system-wide in the venv).
# Copy requirements first to exploit Docker's layer cache — this layer is only
# rebuilt when requirements.txt changes, not on every code change.
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source with correct ownership in one step.
COPY --chown=appuser:appuser . .

# Switch to non-root user for all subsequent instructions and at runtime.
USER appuser

# Expose Flask default port.
EXPOSE 5000

# Default command — overridden per-service in docker-compose.yml.
# Using gunicorn (multi-worker WSGI) instead of Flask's dev server.
# The dev server is fine for the `web` service in development mode
# (overridden below), but gunicorn is the safe default for any other use.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
