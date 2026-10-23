"""
utils.py
--------
Small shared helpers used across the whole application:
window centering, date helpers, message-box wrappers and
a couple of app-wide configurable constants.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------- constants
LOAN_PERIOD_DAYS = 14      # default number of days a book may be borrowed
FINE_PER_DAY = 5.0         # currency units charged per day overdue
DATE_FORMAT = "%Y-%m-%d"


# ------------------------------------------------------------ date helpers
def today_str():
    """Return today's date as YYYY-MM-DD."""
    return date.today().strftime(DATE_FORMAT)


def add_days_str(days, from_date=None):
    """Return (from_date + days) as YYYY-MM-DD. from_date defaults to today."""
    base = date.today() if from_date is None else parse_date(from_date)
    return (base + timedelta(days=days)).strftime(DATE_FORMAT)


def parse_date(text):
    """Parse a YYYY-MM-DD string into a date object. Raises ValueError if bad."""
    return datetime.strptime(text.strip(), DATE_FORMAT).date()


def is_valid_date(text):
    try:
        parse_date(text)
        return True
    except (ValueError, AttributeError):
        return False


def days_overdue(due_date_str, as_of=None):
    """Return number of days a due date is overdue (0 if not overdue)."""
    due = parse_date(due_date_str)
    ref = date.today() if as_of is None else parse_date(as_of)
    delta = (ref - due).days
    return delta if delta > 0 else 0


def calculate_fine(due_date_str, return_date_str=None):
    """Calculate fine based on overdue days. If return_date_str is given,
    overdue is measured against that date, otherwise against today."""
    overdue_days = days_overdue(due_date_str, return_date_str)
    return round(overdue_days * FINE_PER_DAY, 2)


# --------------------------------------------------------- message helpers
def show_error(message, title="Error"):
    messagebox.showerror(title, message)


def show_info(message, title="Success"):
    messagebox.showinfo(title, message)


def show_warning(message, title="Warning"):
    messagebox.showwarning(title, message)


def confirm(message, title="Confirm"):
    return messagebox.askyesno(title, message)


# ---------------------------------------------------------------- windows
def center_window(win, width, height):
    """Center a Tk/Toplevel window on the screen with the given size."""
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def clear_treeview(tree):
    for row in tree.get_children():
        tree.delete(row)
