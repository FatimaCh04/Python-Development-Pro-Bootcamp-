"""
test_vault.py — Comprehensive test suite for VAULT backend

Run with:
    pytest test_vault.py -v

Coverage areas:
  - Crypto primitives (PBKDF2, Fernet encrypt/decrypt)
  - VaultStore (add/search/delete, persistence, encryption at rest)
  - Auth (session management, token expiry)
  - API endpoints (setup, unlock, entries, activity heartbeat)
"""

import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Import modules under test
from crypto import (
    derive_fernet_key,
    encrypt_text,
    decrypt_text,
    generate_salt,
    hash_master_password,
)
from vault_store import VaultStore, WrongMasterPasswordError, EntryNotFoundError
from auth import SessionStore
from main import app


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def temp_vault_path(tmp_path: Path) -> Path:
    """Return a temporary vault.json path that won't touch the real vault."""
    return tmp_path / "test_vault.json"


@pytest.fixture
def vault_store(temp_vault_path: Path) -> VaultStore:
    """Fresh VaultStore instance pointing to a temp file."""
    return VaultStore(vault_path=str(temp_vault_path))


@pytest.fixture
def initialized_vault(vault_store: VaultStore) -> tuple[VaultStore, str]:
    """VaultStore initialized with a known master password."""
    master_pw = "TestMasterPassword123!"
    vault_store.initialize(master_pw)
    return vault_store, master_pw


@pytest.fixture
def session_store() -> SessionStore:
    """Fresh SessionStore with short TTL for faster testing."""
    return SessionStore(ttl=2)  # 2 seconds for expiry tests


@pytest.fixture
def api_client(temp_vault_path: Path, monkeypatch) -> TestClient:
    """
    FastAPI TestClient with a temporary vault path.
    Monkeypatch the global vault instance so API tests don't touch real data.
    Also monkeypatch config to avoid loading .env during tests.
    """
    # Mock config values to avoid .env loading side effects
    monkeypatch.setattr("config.VAULT_PATH", str(temp_vault_path))
    monkeypatch.setattr("config.ALLOWED_ORIGINS", ["http://testclient"])
    monkeypatch.setattr("config.SESSION_TIMEOUT_SECONDS", 300)
    monkeypatch.setattr("config.RATE_LIMIT_MAX_ATTEMPTS", 5)
    monkeypatch.setattr("config.RATE_LIMIT_WINDOW_SECONDS", 300)
    
    from main import vault as original_vault
    test_vault = VaultStore(vault_path=str(temp_vault_path))
    monkeypatch.setattr("main.vault", test_vault)
    return TestClient(app)


# ===========================================================================
# Test: Crypto primitives
# ===========================================================================

class TestCrypto:
    """Test PBKDF2 key derivation and Fernet encryption."""

    def test_salt_generation_is_random(self):
        """Each salt generation produces a unique 16-byte value."""
        salt1 = generate_salt()
        salt2 = generate_salt()
        assert len(salt1) == 16
        assert len(salt2) == 16
        assert salt1 != salt2

    def test_derive_key_deterministic(self):
        """Same password + salt → same key every time."""
        password = "my_secret_password"
        salt = generate_salt()
        key1 = derive_fernet_key(password, salt)
        key2 = derive_fernet_key(password, salt)
        assert key1 == key2

    def test_derive_key_different_with_different_salt(self):
        """Same password + different salt → different key."""
        password = "my_secret_password"
        salt1 = generate_salt()
        salt2 = generate_salt()
        key1 = derive_fernet_key(password, salt1)
        key2 = derive_fernet_key(password, salt2)
        assert key1 != key2

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt returns original plaintext."""
        plaintext = "sensitive_credential_data"
        password = "master_password"
        salt = generate_salt()
        key = derive_fernet_key(password, salt)

        ciphertext = encrypt_text(plaintext, key)
        decrypted = decrypt_text(ciphertext, key)

        assert decrypted == plaintext
        assert ciphertext != plaintext  # ciphertext is opaque

    def test_decrypt_with_wrong_key_raises_error(self):
        """Decrypting with the wrong key raises InvalidToken, not garbage."""
        plaintext = "secret"
        salt = generate_salt()
        key_correct = derive_fernet_key("password1", salt)
        key_wrong = derive_fernet_key("password2", salt)

        ciphertext = encrypt_text(plaintext, key_correct)

        from cryptography.fernet import InvalidToken
        with pytest.raises(InvalidToken):
            decrypt_text(ciphertext, key_wrong)

    def test_master_password_hash_never_equals_raw_password(self):
        """The PBKDF2 hash is never the plaintext password."""
        password = "MyPassword123"
        salt = generate_salt()
        pw_hash = hash_master_password(password, salt)

        assert pw_hash != password
        assert len(pw_hash) == 128  # 64 bytes → 128 hex chars
        assert pw_hash.isalnum()  # hex string

    def test_master_password_hash_deterministic(self):
        """Same password + salt → same hash."""
        password = "MyPassword123"
        salt = generate_salt()
        hash1 = hash_master_password(password, salt)
        hash2 = hash_master_password(password, salt)
        assert hash1 == hash2


# ===========================================================================
# Test: VaultStore (persistence, encryption at rest)
# ===========================================================================

class TestVaultStore:
    """Test vault initialization, add/search/delete, disk persistence."""

    def test_is_initialized_false_when_vault_missing(self, vault_store: VaultStore):
        """is_initialized() returns False before initialize() is called."""
        assert vault_store.is_initialized() is False

    def test_initialize_creates_vault_with_salt_and_hash(
        self, vault_store: VaultStore, temp_vault_path: Path
    ):
        """initialize() writes vault.json with meta.salt and meta.pw_hash."""
        vault_store.initialize("SecurePassword")
        assert vault_store.is_initialized() is True

        # Verify the file was written
        assert temp_vault_path.exists()
        data = json.loads(temp_vault_path.read_text())
        assert "meta" in data
        assert "salt" in data["meta"]
        assert "pw_hash" in data["meta"]
        assert "entries" in data
        assert len(data["entries"]) == 0

    def test_initialize_twice_raises_error(self, initialized_vault):
        """initialize() raises RuntimeError if vault already exists."""
        vault, _ = initialized_vault
        with pytest.raises(RuntimeError, match="already initialized"):
            vault.initialize("AnotherPassword")

    def test_verify_correct_password_returns_true(self, initialized_vault):
        """verify_master_password() returns True for the correct password."""
        vault, master_pw = initialized_vault
        assert vault.verify_master_password(master_pw) is True

    def test_verify_wrong_password_returns_false(self, initialized_vault):
        """verify_master_password() returns False for an incorrect password."""
        vault, _ = initialized_vault
        assert vault.verify_master_password("WrongPassword") is False

    def test_add_entry_returns_uuid(self, initialized_vault):
        """add_entry() returns a UUID string."""
        vault, master_pw = initialized_vault
        entry_id = vault.add_entry(master_pw, "github.com", "alice", "secret123")
        assert isinstance(entry_id, str)
        assert len(entry_id) == 36  # UUID4 format

    def test_add_entry_encrypts_all_fields(self, initialized_vault, temp_vault_path):
        """add_entry() writes encrypted site/username/password to disk."""
        vault, master_pw = initialized_vault
        vault.add_entry(master_pw, "github.com", "alice", "secret123")

        # Read raw vault.json from disk
        data = json.loads(temp_vault_path.read_text())
        entry = data["entries"][0]

        # All fields are ciphertext (Fernet tokens start with 'gAAAAA')
        assert entry["site"] != "github.com"
        assert entry["username"] != "alice"
        assert entry["password"] != "secret123"
        assert "gAAAAA" in entry["site"]  # Fernet token signature
        assert "gAAAAA" in entry["username"]
        assert "gAAAAA" in entry["password"]

    def test_list_entries_decrypts_correctly(self, initialized_vault):
        """list_entries() returns decrypted plaintext."""
        vault, master_pw = initialized_vault
        vault.add_entry(master_pw, "github.com", "alice", "secret123")
        vault.add_entry(master_pw, "gmail.com", "bob", "pass456")

        entries = vault.list_entries(master_pw)
        assert len(entries) == 2
        assert entries[0]["site"] == "github.com"
        assert entries[0]["username"] == "alice"
        assert entries[0]["password"] == "secret123"
        assert entries[1]["site"] == "gmail.com"

    def test_list_entries_with_wrong_password_raises(self, initialized_vault):
        """list_entries() with wrong password raises WrongMasterPasswordError."""
        vault, master_pw = initialized_vault
        vault.add_entry(master_pw, "github.com", "alice", "secret123")

        with pytest.raises(WrongMasterPasswordError):
            vault.list_entries("WrongPassword")

    def test_search_entries_filters_by_site_name(self, initialized_vault):
        """search_entries() returns only matching entries (case-insensitive)."""
        vault, master_pw = initialized_vault
        vault.add_entry(master_pw, "github.com", "alice", "secret123")
        vault.add_entry(master_pw, "gitlab.com", "bob", "pass456")
        vault.add_entry(master_pw, "gmail.com", "charlie", "pw789")

        results = vault.search_entries(master_pw, "git")
        assert len(results) == 2
        sites = {e["site"] for e in results}
        assert sites == {"github.com", "gitlab.com"}

    def test_delete_entry_removes_from_vault(self, initialized_vault):
        """delete_entry() removes the entry from the vault."""
        vault, master_pw = initialized_vault
        entry_id = vault.add_entry(master_pw, "github.com", "alice", "secret123")

        entries_before = vault.list_entries(master_pw)
        assert len(entries_before) == 1

        vault.delete_entry(master_pw, entry_id)

        entries_after = vault.list_entries(master_pw)
        assert len(entries_after) == 0

    def test_delete_nonexistent_entry_raises(self, initialized_vault):
        """delete_entry() with invalid ID raises EntryNotFoundError."""
        vault, master_pw = initialized_vault
        with pytest.raises(EntryNotFoundError):
            vault.delete_entry(master_pw, "nonexistent-uuid")

    def test_vault_survives_restart(self, temp_vault_path):
        """After restart, a new VaultStore can decrypt existing entries."""
        # First session: create vault and add entry
        vault1 = VaultStore(vault_path=str(temp_vault_path))
        vault1.initialize("MasterPass")
        vault1.add_entry("MasterPass", "github.com", "alice", "secret123")

        # Simulate restart: create new VaultStore instance
        vault2 = VaultStore(vault_path=str(temp_vault_path))
        assert vault2.is_initialized() is True
        entries = vault2.list_entries("MasterPass")
        assert len(entries) == 1
        assert entries[0]["site"] == "github.com"
        assert entries[0]["password"] == "secret123"

    def test_update_entry_re_encrypts_fields(self, initialized_vault):
        """update_entry() re-encrypts changed fields."""
        vault, master_pw = initialized_vault
        entry_id = vault.add_entry(master_pw, "github.com", "alice", "secret123")

        vault.update_entry(master_pw, entry_id, password="new_secret")

        entry = vault.get_entry(master_pw, entry_id)
        assert entry["password"] == "new_secret"
        assert entry["username"] == "alice"  # unchanged


# ===========================================================================
# Test: Auth (SessionStore, token expiry)
# ===========================================================================

class TestAuth:
    """Test session token generation, expiry, and idle timeout."""

    def test_create_returns_64_char_hex_token(self, session_store: SessionStore):
        """create() returns a 64-character hex string (32 random bytes)."""
        token = session_store.create("password123")
        assert isinstance(token, str)
        assert len(token) == 64
        assert all(c in "0123456789abcdef" for c in token)

    def test_get_master_password_returns_stored_value(self, session_store: SessionStore):
        """get_master_password() returns the password for a valid token."""
        password = "SecretPassword"
        token = session_store.create(password)
        retrieved = session_store.get_master_password(token)
        assert retrieved == password

    def test_get_master_password_unknown_token_returns_none(self, session_store: SessionStore):
        """get_master_password() returns None for an unknown token."""
        retrieved = session_store.get_master_password("invalid-token-12345")
        assert retrieved is None

    def test_session_expires_after_ttl(self, session_store: SessionStore):
        """Session becomes invalid after TTL (2 seconds in fixture)."""
        token = session_store.create("password123")
        assert session_store.get_master_password(token) == "password123"

        time.sleep(2.1)  # Wait past the 2-second TTL

        retrieved = session_store.get_master_password(token)
        assert retrieved is None

    def test_touch_resets_idle_timer(self, session_store: SessionStore):
        """touch() resets the idle timer so session doesn't expire."""
        token = session_store.create("password123")
        time.sleep(1.5)  # Halfway to expiry
        assert session_store.touch(token) is True
        time.sleep(1.5)  # Another 1.5s (total 3s, but timer was reset at 1.5s)

        # Session should still be valid (only 1.5s since last touch)
        retrieved = session_store.get_master_password(token)
        assert retrieved == "password123"

    def test_destroy_invalidates_session(self, session_store: SessionStore):
        """destroy() removes the session immediately."""
        token = session_store.create("password123")
        assert session_store.get_master_password(token) == "password123"

        session_store.destroy(token)

        retrieved = session_store.get_master_password(token)
        assert retrieved is None

    def test_is_valid_checks_expiry(self, session_store: SessionStore):
        """is_valid() returns False for expired sessions."""
        token = session_store.create("password123")
        assert session_store.is_valid(token) is True

        time.sleep(2.1)

        assert session_store.is_valid(token) is False


# ===========================================================================
# Test: API endpoints (FastAPI TestClient)
# ===========================================================================

class TestAPIEndpoints:
    """Test HTTP API via TestClient: setup, unlock, entries, activity."""

    def test_get_status_returns_initialized_false(self, api_client: TestClient):
        """/api/status returns initialized:false when vault doesn't exist."""
        response = api_client.get("/api/status")
        assert response.status_code == 200
        assert response.json() == {"initialized": False}

    def test_post_setup_creates_vault_and_returns_token(self, api_client: TestClient):
        """/api/setup initializes vault and returns a session token."""
        response = api_client.post(
            "/api/setup",
            json={"master_password": "SecurePassword123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "session_token" in data
        assert len(data["session_token"]) == 64

    def test_post_setup_twice_returns_409(self, api_client: TestClient):
        """/api/setup can only be called once — second call returns 409."""
        api_client.post("/api/setup", json={"master_password": "Pass123"})
        response = api_client.post("/api/setup", json={"master_password": "Pass456"})
        assert response.status_code == 409

    def test_post_setup_short_password_returns_422(self, api_client: TestClient):
        """/api/setup rejects passwords < 8 characters."""
        response = api_client.post("/api/setup", json={"master_password": "short"})
        assert response.status_code == 422

    def test_post_unlock_correct_password_returns_token(self, api_client: TestClient):
        """/api/unlock with correct password returns session token."""
        api_client.post("/api/setup", json={"master_password": "SecurePass123"})
        response = api_client.post("/api/unlock", json={"master_password": "SecurePass123"})
        assert response.status_code == 200
        data = response.json()
        assert "session_token" in data

    def test_post_unlock_wrong_password_returns_401(self, api_client: TestClient):
        """/api/unlock with wrong password returns 401."""
        api_client.post("/api/setup", json={"master_password": "CorrectPass"})
        response = api_client.post("/api/unlock", json={"master_password": "WrongPass"})
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_post_unlock_vault_not_initialized_returns_401(self, api_client: TestClient):
        """/api/unlock returns 401 (not 409) when vault doesn't exist (no info leak)."""
        response = api_client.post("/api/unlock", json={"master_password": "AnyPassword"})
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_get_entries_without_token_returns_422(self, api_client: TestClient):
        """GET /api/entries without X-Session-Token returns 422."""
        api_client.post("/api/setup", json={"master_password": "Pass123"})
        response = api_client.get("/api/entries")
        assert response.status_code == 422  # Missing required header

    def test_get_entries_with_invalid_token_returns_401(self, api_client: TestClient):
        """GET /api/entries with invalid token returns 401."""
        api_client.post("/api/setup", json={"master_password": "Pass123"})
        response = api_client.get(
            "/api/entries",
            headers={"X-Session-Token": "invalid-token-abcd1234"}
        )
        assert response.status_code == 401

    def test_get_entries_with_valid_token_returns_data(self, api_client: TestClient):
        """GET /api/entries with valid token returns decrypted entries."""
        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        # Add an entry
        api_client.post(
            "/api/entries",
            json={"site": "github.com", "username": "alice", "password": "secret"},
            headers={"X-Session-Token": token}
        )

        # List entries
        response = api_client.get("/api/entries", headers={"X-Session-Token": token})
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["site"] == "github.com"

    def test_post_entries_adds_entry(self, api_client: TestClient):
        """POST /api/entries adds a new entry and returns its ID."""
        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        response = api_client.post(
            "/api/entries",
            json={"site": "gitlab.com", "username": "bob", "password": "pw123"},
            headers={"X-Session-Token": token}
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["id"]) == 36  # UUID

    def test_delete_entry_removes_it(self, api_client: TestClient):
        """DELETE /api/entries/{id} removes the entry."""
        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        # Add entry
        add_response = api_client.post(
            "/api/entries",
            json={"site": "example.com", "username": "user", "password": "pw"},
            headers={"X-Session-Token": token}
        )
        entry_id = add_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(
            f"/api/entries/{entry_id}",
            headers={"X-Session-Token": token}
        )
        assert delete_response.status_code == 200

        # Verify it's gone
        list_response = api_client.get("/api/entries", headers={"X-Session-Token": token})
        assert len(list_response.json()["entries"]) == 0

    def test_post_activity_resets_idle_timer(self, api_client: TestClient, monkeypatch):
        """POST /api/activity resets the server-side session timer."""
        # Use a short-lived session store for this test
        from main import session_store as original_store
        test_store = SessionStore(ttl=2)
        monkeypatch.setattr("main.session_store", test_store)

        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        # Wait 1.5 seconds (halfway to expiry)
        time.sleep(1.5)

        # Send heartbeat
        heartbeat_response = api_client.post(
            "/api/activity",
            headers={"X-Session-Token": token}
        )
        assert heartbeat_response.status_code == 200

        # Wait another 1.5 seconds (total 3s, but timer was reset)
        time.sleep(1.5)

        # Session should still be valid (only 1.5s since heartbeat)
        entries_response = api_client.get("/api/entries", headers={"X-Session-Token": token})
        assert entries_response.status_code == 200

    def test_post_activity_expired_token_returns_401(self, api_client: TestClient, monkeypatch):
        """POST /api/activity with expired token returns 401."""
        test_store = SessionStore(ttl=1)
        monkeypatch.setattr("main.session_store", test_store)

        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        time.sleep(1.1)  # Wait past expiry

        response = api_client.post("/api/activity", headers={"X-Session-Token": token})
        assert response.status_code == 401

    def test_post_lock_destroys_session(self, api_client: TestClient):
        """POST /api/lock invalidates the session token."""
        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        # Lock the vault
        lock_response = api_client.post("/api/lock", headers={"X-Session-Token": token})
        assert lock_response.status_code == 200

        # Token is now invalid
        entries_response = api_client.get("/api/entries", headers={"X-Session-Token": token})
        assert entries_response.status_code == 401

    def test_get_entries_with_search_param(self, api_client: TestClient):
        """GET /api/entries?search=xyz filters entries server-side."""
        setup_response = api_client.post("/api/setup", json={"master_password": "Pass123"})
        token = setup_response.json()["session_token"]

        # Add multiple entries
        api_client.post(
            "/api/entries",
            json={"site": "github.com", "username": "alice", "password": "pw1"},
            headers={"X-Session-Token": token}
        )
        api_client.post(
            "/api/entries",
            json={"site": "gitlab.com", "username": "bob", "password": "pw2"},
            headers={"X-Session-Token": token}
        )
        api_client.post(
            "/api/entries",
            json={"site": "gmail.com", "username": "charlie", "password": "pw3"},
            headers={"X-Session-Token": token}
        )

        # Search for "git"
        response = api_client.get(
            "/api/entries?search=git",
            headers={"X-Session-Token": token}
        )
        assert response.status_code == 200
        entries = response.json()["entries"]
        assert len(entries) == 2
        sites = {e["site"] for e in entries}
        assert sites == {"github.com", "gitlab.com"}


# ===========================================================================
# Run with: pytest test_vault.py -v
# ===========================================================================
