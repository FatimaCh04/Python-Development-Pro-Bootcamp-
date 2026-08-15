"""
crypto.py — Key derivation and Fernet encryption helpers.

All encryption uses Fernet (AES-128-CBC + HMAC-SHA256).
Keys are derived from the master password with PBKDF2HMAC so that
no plaintext password ever touches disk.
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# PBKDF2 parameters — 600 000 rounds is OWASP 2023 minimum for SHA-256
_PBKDF2_ITERATIONS = 600_000
_KEY_LENGTH = 32  # bytes → 256-bit key material, base64-encoded to 44 chars for Fernet


def derive_fernet_key(master_password: str, salt: bytes) -> bytes:
    """
    Derive a URL-safe base64-encoded 32-byte Fernet key from a master password
    and a salt using PBKDF2HMAC-SHA256.

    Args:
        master_password: The user's master password (never stored).
        salt: A random 16-byte salt stored alongside the vault metadata.

    Returns:
        A Fernet-compatible key (bytes).
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_LENGTH,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    raw_key = kdf.derive(master_password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def generate_salt() -> bytes:
    """Generate a cryptographically random 16-byte salt."""
    return os.urandom(16)


def encrypt_text(plaintext: str, fernet_key: bytes) -> str:
    """
    Encrypt a UTF-8 string with the given Fernet key.

    Returns:
        URL-safe base64 ciphertext string (Fernet token).
    """
    f = Fernet(fernet_key)
    token = f.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(ciphertext: str, fernet_key: bytes) -> str:
    """
    Decrypt a Fernet token back to a UTF-8 string.

    Raises:
        cryptography.fernet.InvalidToken if the key is wrong or the token
        has been tampered with.
    """
    f = Fernet(fernet_key)
    plaintext = f.decrypt(ciphertext.encode("utf-8"))
    return plaintext.decode("utf-8")


def hash_master_password(master_password: str, salt: bytes) -> str:
    """
    Produce a deterministic hex digest of the master password for
    identity verification purposes.  This is *not* the encryption key —
    it is only used to confirm "correct password" without decrypting the
    whole vault on every unlock call.

    We run PBKDF2 again with a different length so that the verifier
    hash is mathematically independent of the encryption key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=64,          # 512-bit verifier, stored as 128-char hex
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    raw = kdf.derive(master_password.encode("utf-8"))
    return raw.hex()
