"""
config.py — Environment-based configuration for VAULT backend

Loads settings from environment variables with sensible defaults.
Create a .env file in the backend/ directory for local overrides.
"""

import os
from pathlib import Path
from typing import List

# Load .env file if present (for local development)
try:
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
except ImportError:
    # python-dotenv not installed — env vars must be set by the OS
    pass


# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------

def get_allowed_origins() -> List[str]:
    """
    Parse ALLOWED_ORIGINS from environment.
    
    Format: comma-separated list of origins
    Example: http://localhost:8000,https://vault.example.com
    
    Returns empty list if not set (CORS will deny all cross-origin requests).
    """
    origins_str = os.getenv("ALLOWED_ORIGINS", "")
    if not origins_str:
        return []
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


ALLOWED_ORIGINS: List[str] = get_allowed_origins()


# ---------------------------------------------------------------------------
# Session Configuration
# ---------------------------------------------------------------------------

SESSION_TIMEOUT_SECONDS: int = int(os.getenv("SESSION_TIMEOUT_SECONDS", "300"))


# ---------------------------------------------------------------------------
# Vault Storage
# ---------------------------------------------------------------------------

VAULT_PATH: str = os.getenv("VAULT_PATH", "vault.json")

# Resolve relative paths against the backend/ directory
if not os.path.isabs(VAULT_PATH):
    VAULT_PATH = str(Path(__file__).parent / VAULT_PATH)


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

RATE_LIMIT_MAX_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_MAX_ATTEMPTS", "5"))
RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "300"))


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
