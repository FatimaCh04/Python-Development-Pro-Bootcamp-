"""
vault_store.py — Persistent encrypted vault storage.

Layout of vault.json on disk:
{
  "meta": {
    "salt": "<hex-encoded 16-byte salt>",
    "pw_hash": "<hex verifier derived from master password + salt>"
  },
  "entries": [
    {
      "id": "<uuid4>",
      "site": "<Fernet ciphertext>",
      "username": "<Fernet ciphertext>",
      "password": "<Fernet ciphertext>"
    },
    ...
  ]
}

Nothing plaintext ever touches this file.
"""

import json
import os
import secrets
import uuid
from typing import Optional

from cryptography.fernet import InvalidToken

from crypto import (
    derive_fernet_key,
    decrypt_text,
    encrypt_text,
    generate_salt,
    hash_master_password,
)

# ---------------------------------------------------------------------------
# Data classes (plain dicts kept intentionally simple; Pydantic lives in main)
# ---------------------------------------------------------------------------

class VaultNotInitializedError(Exception):
    """Raised when a vault operation is attempted before the vault is set up."""

class WrongMasterPasswordError(Exception):
    """Raised when the supplied master password fails verification."""

class EntryNotFoundError(Exception):
    """Raised when a requested entry ID does not exist in the vault."""


class VaultStore:
    """
    Manages reading and writing the encrypted vault.json file.

    All public methods that need the master password accept it as a
    transient string parameter — it is never persisted to any attribute
    or log.
    """

    def __init__(self, vault_path: str = "vault.json") -> None:
        self._vault_path = vault_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_raw(self) -> dict:
        """Read vault.json and return the parsed dict, or {} if missing."""
        if not os.path.exists(self._vault_path):
            return {}
        with open(self._vault_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_raw(self, data: dict) -> None:
        """Atomically write the vault dict to disk."""
        # Write to a temp file then rename so we never corrupt the vault
        tmp = self._vault_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, self._vault_path)

    def _assert_initialized(self, data: dict) -> None:
        if "meta" not in data:
            raise VaultNotInitializedError(
                "Vault has not been initialized. Call initialize() first."
            )

    def _verify_password(self, master_password: str, data: dict) -> bytes:
        """
        Verify the master password against the stored hash and return the
        derived Fernet key if correct.

        Uses secrets.compare_digest() for constant-time comparison to prevent
        timing attacks that could distinguish "close" vs "wrong" passwords.

        Returns:
            fernet_key (bytes) ready for use with encrypt_text / decrypt_text.

        Raises:
            WrongMasterPasswordError
        """
        salt = bytes.fromhex(data["meta"]["salt"])
        expected_hash = data["meta"]["pw_hash"]
        actual_hash = hash_master_password(master_password, salt)
        
        # Constant-time comparison (requirement #4)
        if not secrets.compare_digest(actual_hash, expected_hash):
            raise WrongMasterPasswordError("Master password is incorrect.")
        
        return derive_fernet_key(master_password, salt)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_initialized(self) -> bool:
        """Return True if the vault file exists and has been set up."""
        data = self._load_raw()
        return "meta" in data

    def initialize(self, master_password: str) -> None:
        """
        Create a fresh vault protected by master_password.

        Raises:
            RuntimeError if the vault is already initialized.
        """
        if self.is_initialized():
            raise RuntimeError(
                "Vault is already initialized. "
                "Delete vault.json to start over."
            )
        salt = generate_salt()
        pw_hash = hash_master_password(master_password, salt)
        data = {
            "meta": {
                "salt": salt.hex(),
                "pw_hash": pw_hash,
            },
            "entries": [],
        }
        self._save_raw(data)

    def verify_master_password(self, master_password: str) -> bool:
        """
        Return True if master_password is correct, False otherwise.
        Does NOT raise — safe to use in auth checks.
        """
        data = self._load_raw()
        if "meta" not in data:
            return False
        try:
            self._verify_password(master_password, data)
            return True
        except WrongMasterPasswordError:
            return False

    def add_entry(
        self,
        master_password: str,
        site: str,
        username: str,
        password: str,
    ) -> str:
        """
        Encrypt and append a new credential entry to the vault.

        Returns:
            The new entry's UUID string.

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError
        """
        data = self._load_raw()
        self._assert_initialized(data)
        fernet_key = self._verify_password(master_password, data)

        entry_id = str(uuid.uuid4())
        data["entries"].append(
            {
                "id": entry_id,
                "site": encrypt_text(site, fernet_key),
                "username": encrypt_text(username, fernet_key),
                "password": encrypt_text(password, fernet_key),
            }
        )
        self._save_raw(data)
        return entry_id

    def list_entries(self, master_password: str) -> list[dict]:
        """
        Decrypt and return all entries as a list of dicts:
            [{"id": ..., "site": ..., "username": ..., "password": ...}, ...]

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError
        """
        data = self._load_raw()
        self._assert_initialized(data)
        fernet_key = self._verify_password(master_password, data)

        result = []
        for enc in data["entries"]:
            try:
                result.append(
                    {
                        "id": enc["id"],
                        "site": decrypt_text(enc["site"], fernet_key),
                        "username": decrypt_text(enc["username"], fernet_key),
                        "password": decrypt_text(enc["password"], fernet_key),
                    }
                )
            except InvalidToken:
                # Skip corrupted entries rather than crashing the whole list
                continue
        return result

    def list_sites(self, master_password: str) -> list[dict]:
        """
        Return only the site name and ID for every entry — passwords and
        usernames are NOT decrypted.  Useful for building a quick index
        without the cost of decrypting every field.

        Returns:
            [{"id": ..., "site": ...}, ...]

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError
        """
        data = self._load_raw()
        self._assert_initialized(data)
        fernet_key = self._verify_password(master_password, data)

        result = []
        for enc in data["entries"]:
            try:
                result.append(
                    {
                        "id": enc["id"],
                        "site": decrypt_text(enc["site"], fernet_key),
                    }
                )
            except InvalidToken:
                continue
        return result

    def search_entries(self, master_password: str, query: str) -> list[dict]:
        """
        Case-insensitive substring search on the decrypted site name.
        Returns full decrypted entries that match.

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError
        """
        query_lower = query.strip().lower()
        return [
            entry
            for entry in self.list_entries(master_password)
            if query_lower in entry["site"].lower()
        ]

    def get_entry(self, master_password: str, entry_id: str) -> dict:
        """
        Decrypt and return a single entry by ID.

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError, EntryNotFoundError
        """
        entries = self.list_entries(master_password)
        for entry in entries:
            if entry["id"] == entry_id:
                return entry
        raise EntryNotFoundError(f"Entry '{entry_id}' not found.")

    def delete_entry(self, master_password: str, entry_id: str) -> None:
        """
        Remove an entry from the vault by ID.

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError, EntryNotFoundError
        """
        data = self._load_raw()
        self._assert_initialized(data)
        self._verify_password(master_password, data)  # auth check

        original_len = len(data["entries"])
        data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
        if len(data["entries"]) == original_len:
            raise EntryNotFoundError(f"Entry '{entry_id}' not found.")
        self._save_raw(data)

    def update_entry(
        self,
        master_password: str,
        entry_id: str,
        site: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Re-encrypt an entry with updated fields. Only non-None fields are changed.

        Raises:
            VaultNotInitializedError, WrongMasterPasswordError, EntryNotFoundError
        """
        data = self._load_raw()
        self._assert_initialized(data)
        fernet_key = self._verify_password(master_password, data)

        for enc in data["entries"]:
            if enc["id"] == entry_id:
                if site is not None:
                    enc["site"] = encrypt_text(site, fernet_key)
                if username is not None:
                    enc["username"] = encrypt_text(username, fernet_key)
                if password is not None:
                    enc["password"] = encrypt_text(password, fernet_key)
                self._save_raw(data)
                return

        raise EntryNotFoundError(f"Entry '{entry_id}' not found.")
