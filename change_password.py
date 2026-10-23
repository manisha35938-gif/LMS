"""
change_password.py
--------------------
Standalone window to let a user change their own password.
"""

import tkinter as tk
from tkinter import ttk

from database import connect_database
from security import verify_password, hash_password
from style import setup_style, COLORS, FONTS
from utils import center_window, show_error, show_info, show_warning
from validators import not_empty

MIN_PASSWORD_LENGTH = 6


class ChangePasswordWindow:
    def __init__(self, root, current_user=None):
        self.root = root
        self.current_user = current_user
        self.root.title("Change Password")
        center_window(self.root, 420, 460)
        self.root.resizable(False, False)
        setup_style(self.root)

        self._build_ui()

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        top_bar = tk.Frame(self.root, bg=COLORS["background"])
        top_bar.pack(fill="x", padx=20, pady=(15, 0))
        ttk.Button(
            top_bar, text="⬅ Back to Dashboard", style="Muted.TButton", command=self._close
        ).pack(anchor="w")

        tk.Label(
            self.root, text="Change Password", bg=COLORS["background"],
            fg=COLORS["primary"], font=FONTS["heading"],
        ).pack(pady=(20, 15))

        form = tk.Frame(self.root, bg=COLORS["background"])
        form.pack(fill="both", expand=True, padx=30)

        tk.Label(form, text="Username", bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
        self.username_entry = ttk.Entry(form, font=FONTS["entry"])
        self.username_entry.pack(fill="x", pady=(2, 12))
        if self.current_user:
            self.username_entry.insert(0, self.current_user)

        tk.Label(form, text="Current Password", bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
        self.current_password_entry = ttk.Entry(form, font=FONTS["entry"], show="*")
        self.current_password_entry.pack(fill="x", pady=(2, 12))
        if self.current_user:
            self.current_password_entry.focus()
        else:
            self.username_entry.focus()

        tk.Label(form, text="New Password", bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
        self.new_password_entry = ttk.Entry(form, font=FONTS["entry"], show="*")
        self.new_password_entry.pack(fill="x", pady=(2, 12))

        tk.Label(form, text="Confirm New Password", bg=COLORS["background"], font=FONTS["label"]).pack(
            anchor="w"
        )
        self.confirm_password_entry = ttk.Entry(form, font=FONTS["entry"], show="*")
        self.confirm_password_entry.pack(fill="x", pady=(2, 20))

        btn_row = tk.Frame(form, bg=COLORS["background"])
        btn_row.pack(fill="x")
        ttk.Button(
            btn_row, text="Change Password", style="Success.TButton", command=self.change_password
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(btn_row, text="Clear", style="Muted.TButton", command=self.clear_form).pack(
            side="left", expand=True, fill="x", padx=(5, 0)
        )

    def clear_form(self):
        if not self.current_user:
            self.username_entry.delete(0, tk.END)
        self.current_password_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)
        self.confirm_password_entry.delete(0, tk.END)

    # --------------------------------------------------------- actions
    def change_password(self):
        username = self.username_entry.get().strip()
        current_password = self.current_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        if not not_empty(username):
            show_warning("Please enter your username.")
            return
        if not current_password:
            show_warning("Please enter your current password.")
            return
        if not new_password:
            show_warning("Please enter a new password.")
            return
        if len(new_password) < MIN_PASSWORD_LENGTH:
            show_warning(f"New password must be at least {MIN_PASSWORD_LENGTH} characters long.")
            return
        if new_password == username:
            show_warning("Password cannot be the same as the username.")
            return
        if new_password != confirm_password:
            show_warning("New passwords do not match.")
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            user = cur.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

            if user is None:
                show_error("Invalid username or password.")
                return

            if not verify_password(current_password, user["password_hash"]):
                show_error("Invalid username or password.")
                return

            cur.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), user["id"]),
            )
            conn.commit()
            show_info("Password changed successfully.")
            self.clear_form()
        except Exception:
            show_error("Unable to change the password. Please try again.")
        finally:
            if conn:
                conn.close()

    def _close(self):
        self.root.destroy()
