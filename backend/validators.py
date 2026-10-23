"""
backend/validators.py
---------------------
Reusable input-validation helpers for both web forms and API requests.
"""

import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def not_empty(text) -> bool:
    """True if text contains at least one non-whitespace character."""
    return text is not None and str(text).strip() != ""


def is_valid_phone(phone) -> bool:
    """Accepts 7-15 digit phone numbers (spaces, dashes, and leading '+' stripped)."""
    if not phone:
        return False
    digits = str(phone).strip().lstrip("+").replace(" ", "").replace("-", "")
    return digits.isdigit() and 7 <= len(digits) <= 15


def is_valid_email(email) -> bool:
    """Empty email is allowed (optional field); if provided it must look valid."""
    if not email:
        return True
    return bool(EMAIL_PATTERN.match(str(email).strip()))


def is_valid_quantity(value) -> bool:
    """True if value is a positive integer."""
    try:
        val = int(value)
        return val > 0
    except (ValueError, TypeError):
        return False


def is_non_negative_int(value) -> bool:
    """True if value is an integer >= 0."""
    try:
        val = int(value)
        return val >= 0
    except (ValueError, TypeError):
        return False


def is_valid_year(value) -> bool:
    """Empty year is allowed; if provided it must be a sane 4-digit year."""
    if value is None or str(value).strip() == "":
        return True
    try:
        year = int(value)
        return 1000 <= year <= 2100
    except (ValueError, TypeError):
        return False


def is_valid_isbn(isbn) -> bool:
    """Empty ISBN is allowed; if provided it must be 8-13 digits (hyphens/spaces ok, 10-digit ending in X/x ok)."""
    if not isbn:
        return True
    cleaned = str(isbn).strip().replace("-", "").replace(" ", "")
    if len(cleaned) == 10 and cleaned[:-1].isdigit() and cleaned[-1] in "0123456789Xx":
        return True
    return cleaned.isdigit() and 8 <= len(cleaned) <= 13
