"""
login.py
---------
Login window. Verifies credentials against the users table and, on
success, closes itself and opens the dashboard.
"""

import tkinter as tk
from tkinter import ttk

from database import connect_database
from security import verify_password
from style import setup_style, COLORS, FONTS
from utils import center_window, show_error, show_warning


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Login")
        center_window(self.root, 420, 480)
        self.root.resizable(False, False)
        setup_style(self.root)

        self.show_password = tk.BooleanVar(value=False)
        self._build_ui()

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        header = tk.Frame(self.root, bg=COLORS["primary"], height=110)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="📚", bg=COLORS["primary"], fg="white", font=("Segoe UI", 30)
        ).pack(pady=(15, 0))
        tk.Label(
            header,
            text="Library Management System",
            bg=COLORS["primary"],
            fg="white",
            font=("Segoe UI", 13, "bold"),
        ).pack()

        form = tk.Frame(self.root, bg=COLORS["background"])
        form.pack(fill="both", expand=True, padx=40, pady=30)

        tk.Label(form, text="Username", bg=COLORS["background"], font=FONTS["label_bold"]).pack(
            anchor="w"
        )
        self.username_entry = ttk.Entry(form, font=FONTS["entry"])
        self.username_entry.pack(fill="x", pady=(4, 15))
        self.username_entry.focus()

        tk.Label(form, text="Password", bg=COLORS["background"], font=FONTS["label_bold"]).pack(
            anchor="w"
        )
        self.password_entry = ttk.Entry(form, font=FONTS["entry"], show="*")
        self.password_entry.pack(fill="x", pady=(4, 4))

        ttk.Checkbutton(
            form,
            text="Show password",
            variable=self.show_password,
            command=self._toggle_password,
        ).pack(anchor="w", pady=(0, 20))

        btn_row = tk.Frame(form, bg=COLORS["background"])
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Login", style="TButton", command=self._attempt_login).pack(
            side="left", expand=True, fill="x", padx=(0, 5)
        )
        ttk.Button(btn_row, text="Clear", style="Muted.TButton", command=self._clear_form).pack(
            side="left", expand=True, fill="x", padx=(5, 0)
        )

        tk.Label(
            form,
            text="Default admin login: admin / admin123",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=FONTS["small"],
        ).pack(pady=(25, 0))

        # Enter in username navigates to password if empty, else submits
        self.username_entry.bind(
            "<Return>",
            lambda event: self.password_entry.focus() if not self.password_entry.get() else self._attempt_login(),
        )
        self.password_entry.bind("<Return>", lambda event: self._attempt_login())
        self.root.bind("<Return>", lambda event: self._attempt_login())

    def _toggle_password(self):
        self.password_entry.config(show="" if self.show_password.get() else "*")

    def _clear_form(self):
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.username_entry.focus()

    # --------------------------------------------------------- actions
    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            show_warning("Please enter both username and password.")
            return

        conn = None
        user = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cur.fetchone()
        except Exception:
            show_error("Unable to connect to the database. Please try again.")
            return
        finally:
            if conn:
                conn.close()

        # Deliberately identical message whether the username or the
        # password was wrong, so we never reveal which one was incorrect.
        if user is None or not verify_password(password, user["password_hash"]):
            show_error("Invalid username or password.")
            self.password_entry.delete(0, tk.END)
            return

        self._open_dashboard(username)

    def _open_dashboard(self, username="admin"):
        self.root.destroy()
        import dashboard

        dashboard_root = tk.Tk()
        dashboard.DashboardWindow(dashboard_root, current_user=username)
        dashboard_root.mainloop()


def main():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
