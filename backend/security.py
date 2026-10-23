"""
backend/security.py
-------------------
Central place for password hashing and verification.
Uses Werkzeug's secure salted password hashing algorithm.
"""

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Return a salted hash of the given plain-text password."""
    return generate_password_hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if the plain-text password matches the stored hash."""
    if not password or not stored_hash:
        return False
    return check_password_hash(stored_hash, password)
