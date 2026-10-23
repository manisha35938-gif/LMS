"""
members.py
-----------
Member management window: add / update / delete / search members,
shown in a Treeview table.
"""

import tkinter as tk
from tkinter import ttk

from database import connect_database
from style import setup_style, COLORS, FONTS
from utils import center_window, show_error, show_info, show_warning, confirm, clear_treeview, today_str
from validators import not_empty, is_valid_phone, is_valid_email

COLUMNS = ("id", "name", "phone", "email", "status", "registration_date")
HEADINGS = ("ID", "Name", "Phone", "Email", "Status", "Registered On")


class MembersWindow:
    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self.selected_id = None

        self.root.title("Members Management")
        center_window(self.root, 950, 620)
        setup_style(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()
        self.load_members()

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        top_bar = tk.Frame(self.root, bg=COLORS["background"])
        top_bar.pack(fill="x", padx=20, pady=(15, 0))
        ttk.Button(
            top_bar, text="⬅ Back to Dashboard", style="Muted.TButton", command=self._close
        ).pack(anchor="w")

        tk.Label(
            self.root, text="Member Management", bg=COLORS["background"],
            fg=COLORS["primary"], font=FONTS["heading"],
        ).pack(anchor="w", padx=20, pady=(10, 5))

        form = tk.Frame(self.root, bg=COLORS["background"])
        form.pack(fill="x", padx=20)

        self.entries = {}
        text_fields = [("Name", "name"), ("Phone", "phone"), ("Email", "email")]
        for i, (label, key) in enumerate(text_fields):
            cell = tk.Frame(form, bg=COLORS["background"])
            cell.grid(row=0, column=i, sticky="ew", padx=6, pady=6)
            form.grid_columnconfigure(i, weight=1)
            tk.Label(cell, text=label, bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
            entry = ttk.Entry(cell, font=FONTS["entry"])
            entry.pack(fill="x")
            self.entries[key] = entry

        addr_cell = tk.Frame(form, bg=COLORS["background"])
        addr_cell.grid(row=1, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        tk.Label(addr_cell, text="Address", bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
        self.address_entry = ttk.Entry(addr_cell, font=FONTS["entry"])
        self.address_entry.pack(fill="x")

        status_cell = tk.Frame(form, bg=COLORS["background"])
        status_cell.grid(row=1, column=2, sticky="ew", padx=6, pady=6)
        tk.Label(status_cell, text="Status", bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
        self.status_combo = ttk.Combobox(
            status_cell, values=["Active", "Inactive"], state="readonly", font=FONTS["entry"]
        )
        self.status_combo.set("Active")
        self.status_combo.pack(fill="x")

        btn_row = tk.Frame(self.root, bg=COLORS["background"])
        btn_row.pack(fill="x", padx=20, pady=10)
        ttk.Button(btn_row, text="Add Member", style="Success.TButton", command=self.add_member).pack(
            side="left", padx=4
        )
        ttk.Button(btn_row, text="Update Member", command=self.update_member).pack(side="left", padx=4)
        ttk.Button(
            btn_row, text="Delete Member", style="Danger.TButton", command=self.delete_member
        ).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Form", style="Muted.TButton", command=self.clear_form).pack(
            side="left", padx=4
        )

        search_row = tk.Frame(self.root, bg=COLORS["background"])
        search_row.pack(fill="x", padx=20, pady=(5, 10))
        tk.Label(search_row, text="Search:", bg=COLORS["background"], font=FONTS["label"]).pack(
            side="left"
        )
        self.search_entry = ttk.Entry(search_row, font=FONTS["entry"])
        self.search_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.search_entry.bind("<Return>", lambda e: self.search_members())
        ttk.Button(search_row, text="Search", command=self.search_members).pack(side="left", padx=4)
        ttk.Button(
            search_row, text="Clear Search", style="Muted.TButton", command=self.load_members
        ).pack(side="left", padx=4)

        table_frame = tk.Frame(self.root, bg=COLORS["background"])
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings")
        for col, heading in zip(COLUMNS, HEADINGS):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=130, anchor="center")
        self.tree.column("name", width=160, anchor="w")
        self.tree.column("email", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ------------------------------------------------------------ data
    def load_members(self):
        self.search_entry.delete(0, tk.END)
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute("SELECT * FROM members ORDER BY id DESC").fetchall()
            self._populate(rows)
        except Exception:
            show_error("Unable to load members. Please try again.")
        finally:
            if conn:
                conn.close()

    def search_members(self):
        term = f"%{self.search_entry.get().strip()}%"
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                "SELECT * FROM members WHERE name LIKE ? OR phone LIKE ? "
                "OR email LIKE ? OR CAST(id AS TEXT) LIKE ? ORDER BY id DESC",
                (term, term, term, term),
            ).fetchall()
            self._populate(rows)
            if not rows:
                show_info("No members matched your search.", title="No Results")
        except Exception:
            show_error("Unable to complete the search. Please try again.")
        finally:
            if conn:
                conn.close()

    def _populate(self, rows):
        clear_treeview(self.tree)
        for row in rows:
            self.tree.insert(
                "", "end",
                values=(
                    row["id"], row["name"], row["phone"] or "", row["email"] or "",
                    row["status"] or "Active", row["registration_date"] or "",
                ),
            )

    def _on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.selected_id = None
            return
        member_id = self.tree.item(selection[0], "values")[0]
        conn = None
        try:
            conn = connect_database()
            row = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
            if row is None:
                return
            self.selected_id = row["id"]
            self.entries["name"].delete(0, tk.END)
            self.entries["name"].insert(0, row["name"])
            self.entries["phone"].delete(0, tk.END)
            self.entries["phone"].insert(0, row["phone"] or "")
            self.entries["email"].delete(0, tk.END)
            self.entries["email"].insert(0, row["email"] or "")
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, row["address"] or "")
            self.status_combo.set(row["status"] or "Active")
        except Exception:
            show_error("Unable to load the selected member.")
        finally:
            if conn:
                conn.close()

    def clear_form(self):
        self.selected_id = None
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.status_combo.set("Active")
        self.tree.selection_remove(self.tree.selection())

    # --------------------------------------------------------- helpers
    def _read_form(self):
        return {
            "name": self.entries["name"].get().strip(),
            "phone": self.entries["phone"].get().strip(),
            "email": self.entries["email"].get().strip(),
            "address": self.address_entry.get().strip(),
            "status": self.status_combo.get() or "Active",
        }

    def _validate(self, data):
        if not not_empty(data["name"]):
            show_warning("Name cannot be empty.")
            return False
        if data["phone"] and not is_valid_phone(data["phone"]):
            show_warning("Please enter a valid phone number (7-15 digits).")
            return False
        if not is_valid_email(data["email"]):
            show_warning("Please enter a valid email address.")
            return False
        return True

    # --------------------------------------------------------- actions
    def add_member(self):
        data = self._read_form()
        if not self._validate(data):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()

            if data["phone"]:
                clash = cur.execute(
                    "SELECT id FROM members WHERE phone = ?", (data["phone"],)
                ).fetchone()
                if clash:
                    show_warning("A member with this phone number already exists.")
                    return
            if data["email"]:
                clash = cur.execute(
                    "SELECT id FROM members WHERE email = ?", (data["email"],)
                ).fetchone()
                if clash:
                    show_warning("A member with this email already exists.")
                    return

            cur.execute(
                """INSERT INTO members (name, phone, email, address, registration_date, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data["name"], data["phone"] or None, data["email"] or None,
                    data["address"] or None, today_str(), data["status"],
                ),
            )
            conn.commit()
            show_info("Member added successfully.")
            self.clear_form()
            self.load_members()
        except Exception:
            show_error("Unable to add the member. Please try again.")
        finally:
            if conn:
                conn.close()

    def update_member(self):
        if self.selected_id is None:
            show_warning("Please select a member from the table to update.")
            return

        data = self._read_form()
        if not self._validate(data):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()

            if data["phone"]:
                clash = cur.execute(
                    "SELECT id FROM members WHERE phone = ? AND id != ?",
                    (data["phone"], self.selected_id),
                ).fetchone()
                if clash:
                    show_warning("A member with this phone number already exists.")
                    return
            if data["email"]:
                clash = cur.execute(
                    "SELECT id FROM members WHERE email = ? AND id != ?",
                    (data["email"], self.selected_id),
                ).fetchone()
                if clash:
                    show_warning("A member with this email already exists.")
                    return

            cur.execute(
                """UPDATE members SET name=?, phone=?, email=?, address=?, status=? WHERE id=?""",
                (
                    data["name"], data["phone"] or None, data["email"] or None,
                    data["address"] or None, data["status"], self.selected_id,
                ),
            )
            conn.commit()
            show_info("Member updated successfully.")
            self.clear_form()
            self.load_members()
        except Exception:
            show_error("Unable to update the member. Please try again.")
        finally:
            if conn:
                conn.close()

    def delete_member(self):
        if self.selected_id is None:
            show_warning("Please select a member from the table to delete.")
            return

        if not confirm("Are you sure you want to delete this member? This will also remove any past loan records for this member."):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            active = cur.execute(
                "SELECT COUNT(*) AS n FROM issued_books WHERE member_id = ? AND status = 'Issued'",
                (self.selected_id,),
            ).fetchone()["n"]

            if active > 0:
                show_warning("Member cannot be deleted because they currently have issued books.")
                return

            # Delete past returned issue records first to ensure foreign key safety
            cur.execute("DELETE FROM issued_books WHERE member_id = ?", (self.selected_id,))
            cur.execute("DELETE FROM members WHERE id = ?", (self.selected_id,))
            conn.commit()
            show_info("Member deleted successfully.")
            self.clear_form()
            self.load_members()
        except Exception:
            show_error("Unable to delete the member. Please try again.")
        finally:
            if conn:
                conn.close()

    def _close(self):
        if self.on_close:
            self.on_close()
        self.root.destroy()
