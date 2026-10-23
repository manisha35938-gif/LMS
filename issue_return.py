"""
issue_return.py
-----------------
Issue / Return workflow. Issuing and returning books are performed as
single database transactions so `books.available` can never drift out
of sync with the `issued_books` records.
"""

import tkinter as tk
from tkinter import ttk

from database import connect_database
from style import setup_style, COLORS, FONTS
from utils import (
    center_window, show_error, show_info, show_warning, confirm,
    clear_treeview, today_str, add_days_str, is_valid_date, calculate_fine,
    LOAN_PERIOD_DAYS,
)

ACTIVE_COLUMNS = ("id", "book", "member", "issue_date", "due_date", "status")
ACTIVE_HEADINGS = ("Issue ID", "Book", "Member", "Issue Date", "Due Date", "Status")

HISTORY_COLUMNS = ("id", "book", "member", "issue_date", "due_date", "return_date", "status", "fine")
HISTORY_HEADINGS = (
    "Issue ID", "Book", "Member", "Issue Date", "Due Date", "Return Date", "Status", "Fine",
)


class IssueReturnWindow:
    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self.selected_active_id = None

        self.root.title("Issue / Return Books")
        center_window(self.root, 1100, 700)
        setup_style(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()
        self.refresh_all()

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        top_bar = tk.Frame(self.root, bg=COLORS["background"])
        top_bar.pack(fill="x", padx=15, pady=(15, 0))
        ttk.Button(
            top_bar, text="⬅ Back to Dashboard", style="Muted.TButton", command=self._close
        ).pack(anchor="w")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.issue_tab = tk.Frame(notebook, bg=COLORS["background"])
        self.return_tab = tk.Frame(notebook, bg=COLORS["background"])
        self.history_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(self.issue_tab, text="Issue Book")
        notebook.add(self.return_tab, text="Return Book")
        notebook.add(self.history_tab, text="History")

        self._build_issue_tab()
        self._build_return_tab()
        self._build_history_tab()

    # --- Issue tab ---------------------------------------------------
    def _build_issue_tab(self):
        form = tk.Frame(self.issue_tab, bg=COLORS["background"])
        form.pack(fill="x", padx=10, pady=15)

        tk.Label(form, text="Member", bg=COLORS["background"], font=FONTS["label_bold"]).grid(
            row=0, column=0, sticky="w", padx=6
        )
        self.member_combo = ttk.Combobox(form, state="readonly", width=40, font=FONTS["entry"])
        self.member_combo.grid(row=1, column=0, padx=6, pady=(2, 10))

        tk.Label(form, text="Book", bg=COLORS["background"], font=FONTS["label_bold"]).grid(
            row=0, column=1, sticky="w", padx=6
        )
        self.book_combo = ttk.Combobox(form, state="readonly", width=40, font=FONTS["entry"])
        self.book_combo.grid(row=1, column=1, padx=6, pady=(2, 10))

        tk.Label(form, text="Issue Date", bg=COLORS["background"], font=FONTS["label_bold"]).grid(
            row=2, column=0, sticky="w", padx=6
        )
        self.issue_date_entry = ttk.Entry(form, font=FONTS["entry"])
        self.issue_date_entry.insert(0, today_str())
        self.issue_date_entry.grid(row=3, column=0, sticky="w", padx=6)

        tk.Label(form, text="Due Date", bg=COLORS["background"], font=FONTS["label_bold"]).grid(
            row=2, column=1, sticky="w", padx=6
        )
        self.due_date_entry = ttk.Entry(form, font=FONTS["entry"])
        self.due_date_entry.insert(0, add_days_str(LOAN_PERIOD_DAYS))
        self.due_date_entry.grid(row=3, column=1, sticky="w", padx=6)

        btn_row = tk.Frame(self.issue_tab, bg=COLORS["background"])
        btn_row.pack(fill="x", padx=16, pady=5)
        ttk.Button(btn_row, text="Issue Book", style="Success.TButton", command=self.issue_book).pack(
            side="left"
        )
        ttk.Button(
            btn_row, text="Refresh Lists", style="Muted.TButton", command=self.refresh_all
        ).pack(side="left", padx=8)

    # --- Return tab ----------------------------------------------------
    def _build_return_tab(self):
        table_frame = tk.Frame(self.return_tab, bg=COLORS["background"])
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.active_tree = ttk.Treeview(table_frame, columns=ACTIVE_COLUMNS, show="headings")
        for col, heading in zip(ACTIVE_COLUMNS, ACTIVE_HEADINGS):
            self.active_tree.heading(col, text=heading)
            self.active_tree.column(col, width=140, anchor="center")
        self.active_tree.column("book", width=200, anchor="w")
        self.active_tree.column("member", width=160, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.active_tree.yview)
        self.active_tree.configure(yscrollcommand=scrollbar.set)
        self.active_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.active_tree.bind("<<TreeviewSelect>>", self._on_active_select)

        btn_row = tk.Frame(self.return_tab, bg=COLORS["background"])
        btn_row.pack(fill="x", padx=16, pady=10)
        ttk.Button(
            btn_row, text="Return Selected Book", style="Success.TButton", command=self.return_book
        ).pack(side="left")
        ttk.Button(
            btn_row, text="Refresh", style="Muted.TButton", command=self.refresh_all
        ).pack(side="left", padx=8)

    # --- History tab -----------------------------------------------
    def _build_history_tab(self):
        filter_row = tk.Frame(self.history_tab, bg=COLORS["background"])
        filter_row.pack(fill="x", padx=10, pady=10)

        tk.Label(filter_row, text="Member/Book contains:", bg=COLORS["background"], font=FONTS["label"]).pack(
            side="left"
        )
        self.history_search_entry = ttk.Entry(filter_row, font=FONTS["entry"], width=25)
        self.history_search_entry.pack(side="left", padx=6)

        tk.Label(filter_row, text="Status:", bg=COLORS["background"], font=FONTS["label"]).pack(
            side="left", padx=(10, 0)
        )
        self.status_filter = ttk.Combobox(
            filter_row, values=["All", "Issued", "Returned"], state="readonly", width=12
        )
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=6)

        ttk.Button(filter_row, text="Search", command=self.search_history).pack(side="left", padx=6)
        ttk.Button(
            filter_row, text="Clear Search", style="Muted.TButton", command=self.load_history
        ).pack(side="left")

        table_frame = tk.Frame(self.history_tab, bg=COLORS["background"])
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.history_tree = ttk.Treeview(table_frame, columns=HISTORY_COLUMNS, show="headings")
        for col, heading in zip(HISTORY_COLUMNS, HISTORY_HEADINGS):
            self.history_tree.heading(col, text=heading)
            self.history_tree.column(col, width=110, anchor="center")
        self.history_tree.column("book", width=180, anchor="w")
        self.history_tree.column("member", width=140, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ------------------------------------------------------------ data
    def refresh_all(self):
        self._load_combo_data()
        self.load_active_issues()
        self.load_history()

    def _load_combo_data(self):
        conn = None
        try:
            conn = connect_database()
            self.members = conn.execute(
                "SELECT id, name FROM members WHERE status = 'Active' OR status IS NULL ORDER BY name"
            ).fetchall()
            self.books = conn.execute(
                "SELECT id, title, available FROM books WHERE available > 0 ORDER BY title"
            ).fetchall()
        except Exception:
            show_error("Unable to load members/books. Please try again.")
            self.members, self.books = [], []
        finally:
            if conn:
                conn.close()

        self.member_combo["values"] = [f"{m['id']} - {m['name']}" for m in self.members]
        self.book_combo["values"] = [
            f"{b['id']} - {b['title']} ({b['available']} available)" for b in self.books
        ]

    def load_active_issues(self):
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                """SELECT ib.id, b.title AS book, m.name AS member,
                          ib.issue_date, ib.due_date, ib.status
                   FROM issued_books ib
                   JOIN books b ON b.id = ib.book_id
                   JOIN members m ON m.id = ib.member_id
                   WHERE ib.status = 'Issued'
                   ORDER BY ib.due_date ASC"""
            ).fetchall()
        except Exception:
            show_error("Unable to load active issues. Please try again.")
            return
        finally:
            if conn:
                conn.close()

        clear_treeview(self.active_tree)
        today = today_str()
        for row in rows:
            status = "Overdue" if row["due_date"] < today else "Issued"
            self.active_tree.insert(
                "", "end",
                values=(row["id"], row["book"], row["member"], row["issue_date"], row["due_date"], status),
            )

    def load_history(self):
        self.history_search_entry.delete(0, tk.END)
        self.status_filter.set("All")
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                """SELECT ib.id, b.title AS book, m.name AS member, ib.issue_date,
                          ib.due_date, ib.return_date, ib.status, ib.fine
                   FROM issued_books ib
                   JOIN books b ON b.id = ib.book_id
                   JOIN members m ON m.id = ib.member_id
                   ORDER BY ib.id DESC"""
            ).fetchall()
        except Exception:
            show_error("Unable to load issue history. Please try again.")
            return
        finally:
            if conn:
                conn.close()
        self._populate_history(rows)

    def search_history(self):
        term = f"%{self.history_search_entry.get().strip()}%"
        status = self.status_filter.get()
        conn = None
        try:
            conn = connect_database()
            query = """SELECT ib.id, b.title AS book, m.name AS member, ib.issue_date,
                              ib.due_date, ib.return_date, ib.status, ib.fine
                       FROM issued_books ib
                       JOIN books b ON b.id = ib.book_id
                       JOIN members m ON m.id = ib.member_id
                       WHERE (b.title LIKE ? OR m.name LIKE ?)"""
            params = [term, term]
            if status != "All":
                query += " AND ib.status = ?"
                params.append(status)
            query += " ORDER BY ib.id DESC"
            rows = conn.execute(query, params).fetchall()
        except Exception:
            show_error("Unable to complete the search. Please try again.")
            return
        finally:
            if conn:
                conn.close()
        self._populate_history(rows)
        if not rows:
            show_info("No matching records found.", title="No Results")

    def _populate_history(self, rows):
        clear_treeview(self.history_tree)
        for row in rows:
            fine_val = f"₹{row['fine']:.2f}" if row["fine"] else "₹0.00"
            self.history_tree.insert(
                "", "end",
                values=(
                    row["id"], row["book"], row["member"], row["issue_date"],
                    row["due_date"], row["return_date"] or "-", row["status"], fine_val,
                ),
            )

    def _on_active_select(self, event):
        selection = self.active_tree.selection()
        if selection:
            self.selected_active_id = self.active_tree.item(selection[0], "values")[0]
        else:
            self.selected_active_id = None

    # --------------------------------------------------------- actions
    def issue_book(self):
        member_sel = self.member_combo.get()
        book_sel = self.book_combo.get()
        issue_date = self.issue_date_entry.get().strip()
        due_date = self.due_date_entry.get().strip()

        if not member_sel or not book_sel:
            show_warning("Please select both a member and a book.")
            return
        if not is_valid_date(issue_date) or not is_valid_date(due_date):
            show_warning("Please enter valid dates in YYYY-MM-DD format.")
            return
        if due_date < issue_date:
            show_warning("Due date cannot be earlier than the issue date.")
            return

        try:
            member_id = int(member_sel.split(" - ")[0])
            book_id = int(book_sel.split(" - ")[0])
        except (ValueError, IndexError):
            show_warning("Please select a valid member and book from the list.")
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            # --- transaction start ---
            book = cur.execute("SELECT available FROM books WHERE id = ?", (book_id,)).fetchone()
            if book is None:
                show_error("Selected book no longer exists.")
                return
            if book["available"] <= 0:
                show_warning("This book is currently unavailable.")
                return

            already_issued = cur.execute(
                "SELECT id FROM issued_books WHERE book_id = ? AND member_id = ? AND status = 'Issued'",
                (book_id, member_id),
            ).fetchone()
            if already_issued:
                show_warning("This member already has this book issued.")
                return

            cur.execute(
                """INSERT INTO issued_books (book_id, member_id, issue_date, due_date, status, fine)
                   VALUES (?, ?, ?, ?, 'Issued', 0)""",
                (book_id, member_id, issue_date, due_date),
            )
            cur.execute("UPDATE books SET available = available - 1 WHERE id = ?", (book_id,))
            conn.commit()
            # --- transaction end ---
            show_info("Book issued successfully.")
            self.issue_date_entry.delete(0, tk.END)
            self.issue_date_entry.insert(0, today_str())
            self.due_date_entry.delete(0, tk.END)
            self.due_date_entry.insert(0, add_days_str(LOAN_PERIOD_DAYS))
            self.refresh_all()
        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            show_error("Unable to complete the issue operation. Please try again.")
        finally:
            if conn:
                conn.close()

    def return_book(self):
        if self.selected_active_id is None:
            show_warning("Please select an issued book from the list to return.")
            return

        if not confirm("Confirm return of this book?", title="Confirm Return"):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            # --- transaction start ---
            record = cur.execute(
                "SELECT * FROM issued_books WHERE id = ?", (self.selected_active_id,)
            ).fetchone()
            if record is None:
                show_error("Record not found.")
                return
            if record["status"] == "Returned":
                show_warning("This book has already been returned.")
                return

            return_date = today_str()
            fine = calculate_fine(record["due_date"], return_date)

            cur.execute(
                "UPDATE issued_books SET return_date = ?, status = 'Returned', fine = ? WHERE id = ?",
                (return_date, fine, self.selected_active_id),
            )
            cur.execute(
                "UPDATE books SET available = MIN(quantity, available + 1) WHERE id = ?", (record["book_id"],)
            )
            conn.commit()
            # --- transaction end ---

            if fine > 0:
                show_info(f"Book returned successfully. Overdue fine: ₹{fine:.2f}")
            else:
                show_info("Book returned successfully.")

            self.selected_active_id = None
            self.refresh_all()
        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            show_error("Unable to complete the return operation. Please try again.")
        finally:
            if conn:
                conn.close()

    def _close(self):
        if self.on_close:
            self.on_close()
        self.root.destroy()
