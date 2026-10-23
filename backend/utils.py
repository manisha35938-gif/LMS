"""
backend/utils.py
----------------
Shared business logic helpers: date parsing, loan periods, overdue calculation,
fine calculation, and currency formatting.
"""

from datetime import date, datetime, timedelta

# ---------------------------------------------------------------- constants
LOAN_PERIOD_DAYS = 14      # default days a book may be borrowed
FINE_PER_DAY = 5.0         # currency charged per overdue day (₹5.00)
DATE_FORMAT = "%Y-%m-%d"


def today_str() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().strftime(DATE_FORMAT)


def add_days_str(days: int, from_date: str = None) -> str:
    """Return (from_date + days) as YYYY-MM-DD string."""
    base = date.today() if from_date is None else parse_date(from_date)
    return (base + timedelta(days=days)).strftime(DATE_FORMAT)


def parse_date(text: str) -> date:
    """Parse a YYYY-MM-DD string into a date object."""
    return datetime.strptime(str(text).strip(), DATE_FORMAT).date()


def is_valid_date(text: str) -> bool:
    """Return True if text matches YYYY-MM-DD."""
    try:
        parse_date(text)
        return True
    except (ValueError, AttributeError):
        return False


def days_overdue(due_date_str: str, as_of: str = None) -> int:
    """Return number of days a due date is overdue (0 if not overdue)."""
    try:
        due = parse_date(due_date_str)
        ref = date.today() if as_of is None else parse_date(as_of)
        delta = (ref - due).days
        return delta if delta > 0 else 0
    except Exception:
        return 0


def calculate_fine(due_date_str: str, return_date_str: str = None) -> float:
    """Calculate fine based on overdue days at FINE_PER_DAY rate."""
    overdue_days = days_overdue(due_date_str, return_date_str)
    return round(overdue_days * FINE_PER_DAY, 2)


def format_currency(amount: float) -> str:
    """Format amount as ₹0.00."""
    try:
        return f"₹{float(amount):.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

