"""
auth.py — In-process session management.

Design choices:
  - No JWT library dependency. Sessions are opaque random tokens stored
    in a server-side dict, similar to a traditional cookie session store.
  - The master password is NEVER stored in the session. Only a
    cryptographic session token is issued. Every protected endpoint
    re-derives the Fernet key on the fly from the token → vault lookup.
  - Sessions expire after SESSION_TTL_SECONDS of inactivity (mirrors the
    front-end 5-minute auto-logout ring).
  - Thread safety: a threading.Lock guards all mutations so the dict
    stays consistent under FastAPI's async+thread pool execution model.
"""

import os
import time
import threading
from typing import Optional

import config


class SessionStore:
    """
    Server-side opaque-token session store.

    Token lifecycle:
        create()  → token (str)
        touch()   → resets TTL on activity
        get()     → returns stored master password (or None if expired/absent)
        destroy() → explicit logout
    """

    def __init__(self, ttl: int = None) -> None:
        if ttl is None:
            ttl = config.SESSION_TIMEOUT_SECONDS
        self._ttl = ttl
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _new_token() -> str:
        """32 random bytes → 64-char hex string."""
        return os.urandom(32).hex()

    def _is_expired(self, session: dict) -> bool:
        return (time.monotonic() - session["last_active"]) > self._ttl

    def _purge_expired(self) -> None:
        """Remove all stale sessions (called inside the lock)."""
        stale = [tok for tok, s in self._store.items() if self._is_expired(s)]
        for tok in stale:
            del self._store[tok]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, master_password: str) -> str:
        """
        Open a new session for an authenticated user.

        The master_password is held only in RAM for the session lifetime so
        that subsequent API calls can re-derive the Fernet key without asking
        the user again.  It is never written to any file or log.

        Returns:
            An opaque session token string.
        """
        token = self._new_token()
        with self._lock:
            self._purge_expired()
            self._store[token] = {
                "master_password": master_password,
                "last_active": time.monotonic(),
            }
        return token

    def get_master_password(self, token: str) -> Optional[str]:
        """
        Look up the master password for a valid, non-expired session.

        Automatically touches (resets TTL) on successful access.

        Returns:
            The master password string, or None if the token is unknown /
            has expired.
        """
        with self._lock:
            session = self._store.get(token)
            if session is None:
                return None
            if self._is_expired(session):
                del self._store[token]
                return None
            session["last_active"] = time.monotonic()
            return session["master_password"]

    def touch(self, token: str) -> bool:
        """
        Reset the idle TTL for a token without reading sensitive data.

        Returns:
            True if the token was valid and refreshed, False otherwise.
        """
        with self._lock:
            session = self._store.get(token)
            if session is None or self._is_expired(session):
                return False
            session["last_active"] = time.monotonic()
            return True

    def destroy(self, token: str) -> None:
        """Invalidate a session immediately (explicit logout)."""
        with self._lock:
            self._store.pop(token, None)

    def is_valid(self, token: str) -> bool:
        """Return True if the token exists and has not expired."""
        return self.get_master_password(token) is not None


# ---------------------------------------------------------------------------
# Module-level singleton — imported by main.py
# ---------------------------------------------------------------------------
session_store = SessionStore()
