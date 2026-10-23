"""
security.py
------------
Central place for password hashing. No other module should hash or verify
passwords directly - everything goes through hash_password()/verify_password()
so the hashing algorithm can be changed in exactly one place if needed.
"""

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password):
    """Return a salted hash of the given plain-text password."""
    return generate_password_hash(password)


def verify_password(password, stored_hash):
    """Return True if the plain-text password matches the stored hash."""
    return check_password_hash(stored_hash, password)
