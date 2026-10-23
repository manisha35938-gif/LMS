"""
desktop/utils.py
----------------
Tkinter GUI dialog and window helpers for the desktop application.
Imports business logic (dates, fines) from backend.utils.
"""

from tkinter import messagebox
from backend.utils import (
    today_str, add_days_str, parse_date, is_valid_date,
    days_overdue, calculate_fine, LOAN_PERIOD_DAYS, FINE_PER_DAY
)


def show_error(message, title="Error"):
    messagebox.showerror(title, message)


def show_info(message, title="Success"):
    messagebox.showinfo(title, message)


def show_warning(message, title="Warning"):
    messagebox.showwarning(title, message)


def confirm(message, title="Confirm"):
    return messagebox.askyesno(title, message)


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

