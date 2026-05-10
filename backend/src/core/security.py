"""Security helpers for authentication and secret generation.

This module keeps the low-level password and token primitives in one place so
the rest of the backend can stay focused on request handling and persistence.
"""

from __future__ import annotations

import secrets
from typing import Final

import bcrypt

MIN_TOKEN_BYTES: Final[int] = 16
DEFAULT_TOKEN_BYTES: Final[int] = 32


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""

    if not password:
        raise ValueError("Password cannot be empty")

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""

    if not password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def generate_secure_token(length: int = DEFAULT_TOKEN_BYTES) -> str:
    """Generate a URL-safe random token for API secrets or one-time keys."""

    if length < MIN_TOKEN_BYTES:
        raise ValueError(f"Token length must be at least {MIN_TOKEN_BYTES} bytes")

    return secrets.token_urlsafe(length)