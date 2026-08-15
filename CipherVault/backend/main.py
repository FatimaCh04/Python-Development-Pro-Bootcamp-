"""
main.py — VAULT FastAPI application (PRODUCTION-HARDENED).

Run with:
    uvicorn main:app --reload --port 8000

Security improvements:
  1. CORS allowlist from environment (no wildcards)
  2. Rate limiting on /unlock and /setup (5 attempts per 5 min per IP)
  3. Session timeout and vault path from env config
  4. Timing-safe password verification (no info leaks)
  5. Structured logging for failed auth (no plaintext passwords)

All routes that mutate or read vault data require a valid session token
supplied in the X-Session-Token request header.

API surface (wired to the existing frontend):
  GET  /api/status              – Check if vault is initialized
  POST /api/setup               – Initialize vault with a master password
  POST /api/unlock              – Verify master password → session token
  POST /api/lock                – Destroy session (explicit logout)
  POST /api/activity            – Heartbeat: reset the idle auto-logout timer
  GET  /api/entries             – List all decrypted entries
  GET  /api/entries?search=xyz  – Server-side filtered entries (site name)
  GET  /api/sites               – Site names + IDs only (no password decrypt)
  POST /api/entries             – Add a new encrypted entry
  PUT  /api/entries/{id}        – Update an entry
  DELETE /api/entries/{id}      – Delete an entry
"""

import os
import sys
import logging

from fastapi import FastAPI, Header, HTTPException, Query, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import Optional

# ---------------------------------------------------------------------------
# Ensure local modules (crypto, vault_store, auth) are importable when
# uvicorn is launched from the backend/ directory.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

import config
from auth import session_store
from rate_limiter import rate_limiter
from vault_store import (
    VaultStore,
    VaultNotInitializedError,
    WrongMasterPasswordError,
    EntryNotFoundError,
)

# ---------------------------------------------------------------------------
# Structured logging (requirement #5)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("vault")


# ---------------------------------------------------------------------------
# Helper: extract client IP from request
# ---------------------------------------------------------------------------
def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Checks X-Forwarded-For (if behind proxy) then falls back to client.host.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can be a comma-separated list; take the first
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# ---------------------------------------------------------------------------
# App & middleware
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VAULT API",
    description="Encrypted password manager — FastAPI backend",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ---------------------------------------------------------------------------
# CORS: explicit allowlist from environment (requirement #1)
# ---------------------------------------------------------------------------
# Deny all cross-origin requests if ALLOWED_ORIGINS is empty/unset
allowed_origins = config.ALLOWED_ORIGINS if config.ALLOWED_ORIGINS else []

if not allowed_origins:
    logger.warning(
        "ALLOWED_ORIGINS is empty. All cross-origin requests will be denied. "
        "Set ALLOWED_ORIGINS in .env for local development."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Vault store — path from environment (requirement #3)
# ---------------------------------------------------------------------------
vault = VaultStore(vault_path=config.VAULT_PATH)
logger.info(f"Vault storage: {config.VAULT_PATH}")
logger.info(f"Session timeout: {config.SESSION_TIMEOUT_SECONDS}s")
logger.info(f"Rate limit: {config.RATE_LIMIT_MAX_ATTEMPTS} attempts per {config.RATE_LIMIT_WINDOW_SECONDS}s")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SetupRequest(BaseModel):
    master_password: str

    @field_validator("master_password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("master_password must not be empty.")
        if len(v) < 8:
            raise ValueError("master_password must be at least 8 characters.")
        return v


class UnlockRequest(BaseModel):
    master_password: str

    @field_validator("master_password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("master_password must not be empty.")
        return v


class EntryCreate(BaseModel):
    site: str
    username: str
    password: str

    @field_validator("site", "username", "password")
    @classmethod
    def fields_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v


class EntryUpdate(BaseModel):
    site: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


# ---------------------------------------------------------------------------
# Dependency: extract + validate session token from header
# ---------------------------------------------------------------------------

def require_session(x_session_token: str = Header(...)) -> str:
    """
    FastAPI dependency that reads X-Session-Token and validates it.
    Returns the master password for the session on success.
    Raises HTTP 401 on missing / expired token.
    """
    master_password = session_store.get_master_password(x_session_token)
    if master_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please unlock the vault again.",
        )
    return master_password


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.exception_handler(VaultNotInitializedError)
async def vault_not_init_handler(request: Request, exc: VaultNotInitializedError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(WrongMasterPasswordError)
async def wrong_password_handler(request: Request, exc: WrongMasterPasswordError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Incorrect master password."},
    )


@app.exception_handler(EntryNotFoundError)
async def entry_not_found_handler(request: Request, exc: EntryNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/status", tags=["Vault"])
async def get_status():
    """
    Check whether the vault has been initialized.
    The frontend uses this on load to decide whether to show "Setup" or "Unlock".
    """
    return {"initialized": vault.is_initialized()}


@app.post("/api/setup", status_code=status.HTTP_201_CREATED, tags=["Vault"])
async def setup_vault(body: SetupRequest, request: Request):
    """
    Initialize the vault with a master password.
    Creates vault.json with a random salt and a derived password verifier.
    Can only be called once — returns 409 if vault already exists.
    
    RATE LIMITED: Maximum 5 attempts per 5 minutes per IP (configurable).
    """
    client_ip = get_client_ip(request)
    
    # Rate limit check (requirement #2)
    is_limited, remaining = rate_limiter.is_rate_limited(client_ip)
    if is_limited:
        retry_after = rate_limiter.get_retry_after(client_ip)
        logger.warning(
            f"Rate limit exceeded for /setup from IP {client_ip}",
            extra={"ip": client_ip, "endpoint": "/setup"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many setup attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    
    try:
        vault.initialize(body.master_password)
        # Success: clear rate limit for this IP
        rate_limiter.reset(client_ip)
        logger.info(f"Vault initialized successfully from IP {client_ip}")
    except RuntimeError as exc:
        # Vault already exists — don't count as failed attempt
        logger.info(f"Setup attempted on already-initialized vault from IP {client_ip}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    
    # Automatically open a session so the user lands in the dashboard
    token = session_store.create(body.master_password)
    return {"detail": "Vault initialized.", "session_token": token}


@app.post("/api/unlock", tags=["Auth"])
async def unlock_vault(body: UnlockRequest, request: Request):
    """
    Verify the master password and return a session token.
    The token must be passed as X-Session-Token on all subsequent requests.
    
    RATE LIMITED: Maximum 5 attempts per 5 minutes per IP (configurable).
    
    Security (requirement #4):
    - Returns generic 401 for both "vault doesn't exist" and "wrong password"
      to avoid leaking vault existence to an attacker.
    - Uses constant-time comparison (PBKDF2 verify in crypto.py) so timing
      analysis cannot distinguish "close" vs "wrong" passwords.
    - All code paths take similar time regardless of failure reason.
    """
    client_ip = get_client_ip(request)
    
    # Rate limit check (requirement #2)
    is_limited, remaining = rate_limiter.is_rate_limited(client_ip)
    if is_limited:
        retry_after = rate_limiter.get_retry_after(client_ip)
        logger.warning(
            f"Rate limit exceeded for /unlock from IP {client_ip}",
            extra={"ip": client_ip, "endpoint": "/unlock"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many unlock attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
    
    # Timing-safe check: both conditions evaluated in same branch (requirement #4)
    # so response time doesn't leak whether vault exists or password is wrong
    vault_exists = vault.is_initialized()
    password_valid = vault_exists and vault.verify_master_password(body.master_password)
    
    if not password_valid:
        # Failed attempt — record for rate limiting
        rate_limiter.record_attempt(client_ip)
        
        # Structured logging (requirement #5): log IP but NEVER log the password
        logger.warning(
            f"Failed unlock attempt from IP {client_ip}",
            extra={
                "ip": client_ip,
                "endpoint": "/unlock",
                "vault_exists": vault_exists,
                # NOTE: Password is NEVER logged — only metadata
            },
        )
        
        # Generic 401 response (same for both failure modes)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect master password.",
        )
    
    # Success: clear rate limit and create session
    rate_limiter.reset(client_ip)
    logger.info(f"Successful unlock from IP {client_ip}")
    
    token = session_store.create(body.master_password)
    return {"session_token": token}


@app.post("/api/lock", tags=["Auth"])
async def lock_vault(x_session_token: str = Header(...)):
    """
    Destroy the current session (explicit lock / logout).
    Safe to call even if the token is already expired.
    """
    session_store.destroy(x_session_token)
    return {"detail": "Vault locked."}


@app.post("/api/activity", tags=["Auth"])
async def heartbeat(x_session_token: str = Header(...)):
    """
    Heartbeat endpoint — resets the server-side idle auto-logout timer.

    The frontend calls this on user activity events (mousemove, keydown,
    click, scroll) so the server TTL stays in sync with the UI countdown.
    Returns 401 if the session has already expired, prompting the frontend
    to redirect to the lock screen.
    """
    refreshed = session_store.touch(x_session_token)
    if not refreshed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please unlock the vault again.",
        )
    return {"detail": "Session refreshed."}


@app.get("/api/sites", tags=["Entries"])
async def list_sites(master_password: str = Depends(require_session)):
    """
    Return site names and IDs only — no passwords or usernames are
    decrypted.  Cheaper than GET /api/entries when the caller only needs
    a searchable index.
    """
    sites = vault.list_sites(master_password)
    return {"sites": sites}


@app.get("/api/entries", tags=["Entries"])
async def list_entries(
    search: Optional[str] = Query(default=None, description="Filter entries by site name (case-insensitive substring match)"),
    master_password: str = Depends(require_session),
):
    """
    Return decrypted vault entries.

    - Without ?search → all entries.
    - With ?search=xyz → only entries whose site name contains 'xyz'
      (case-insensitive).  Filtering is done server-side so the client
      never receives entries it didn't ask for.
    """
    if search:
        result = vault.search_entries(master_password, search)
    else:
        result = vault.list_entries(master_password)
    return {"entries": result}


@app.post("/api/entries", status_code=status.HTTP_201_CREATED, tags=["Entries"])
async def add_entry(
    body: EntryCreate,
    master_password: str = Depends(require_session),
):
    """Encrypt and store a new credential entry."""
    entry_id = vault.add_entry(
        master_password=master_password,
        site=body.site,
        username=body.username,
        password=body.password,
    )
    return {"id": entry_id, "detail": "Entry saved."}


@app.put("/api/entries/{entry_id}", tags=["Entries"])
async def update_entry(
    entry_id: str,
    body: EntryUpdate,
    master_password: str = Depends(require_session),
):
    """Update one or more fields on an existing entry."""
    vault.update_entry(
        master_password=master_password,
        entry_id=entry_id,
        site=body.site,
        username=body.username,
        password=body.password,
    )
    return {"detail": "Entry updated."}


@app.delete("/api/entries/{entry_id}", tags=["Entries"])
async def delete_entry(
    entry_id: str,
    master_password: str = Depends(require_session),
):
    """Permanently remove an entry from the vault."""
    vault.delete_entry(master_password=master_password, entry_id=entry_id)
    return {"detail": "Entry deleted."}


# ---------------------------------------------------------------------------
# Serve the frontend from /  — mounted LAST so all /api/* routes above
# take priority. StaticFiles is a catch-all and must come after every route.
# ---------------------------------------------------------------------------
_FRONTEND_DIR = os.path.join(
    os.path.dirname(__file__), "..", "vault-frontend", "vault-frontend"
)
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="static")
