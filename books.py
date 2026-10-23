"""
books.py
---------
Book management window: add / update / delete / search books, shown
in a Treeview table. Handles all book-related validation and keeps
`available` quantity consistent with `quantity`.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from database import connect_database
from style import setup_style, COLORS, FONTS
from utils import center_window, show_error, show_info, show_warning, confirm, clear_treeview
from validators import not_empty, is_valid_quantity, is_valid_year, is_valid_isbn

COLUMNS = ("id", "isbn", "title", "author", "category", "quantity", "available", "shelf")
HEADINGS = ("ID", "ISBN", "Title", "Author", "Category", "Qty", "Available", "Shelf")


class BooksWindow:
    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self.selected_id = None

        self.root.title("Books Management")
        center_window(self.root, 1050, 650)
        setup_style(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()
        self.load_books()

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        top_bar = tk.Frame(self.root, bg=COLORS["background"])
        top_bar.pack(fill="x", padx=20, pady=(15, 0))
        ttk.Button(
            top_bar, text="⬅ Back to Dashboard", style="Muted.TButton", command=self._close
        ).pack(anchor="w")

        tk.Label(
            self.root, text="Book Management", bg=COLORS["background"],
            fg=COLORS["primary"], font=FONTS["heading"],
        ).pack(anchor="w", padx=20, pady=(10, 5))

        form = tk.Frame(self.root, bg=COLORS["background"])
        form.pack(fill="x", padx=20)

        self.entries = {}
        fields = [
            ("ISBN", "isbn"), ("Title", "title"), ("Author", "author"),
            ("Category", "category"), ("Publisher", "publisher"),
            ("Publication Year", "publication_year"), ("Quantity", "quantity"),
            ("Shelf / Rack", "shelf"),
        ]
        for i, (label, key) in enumerate(fields):
            row, col = divmod(i, 4)
            cell = tk.Frame(form, bg=COLORS["background"])
            cell.grid(row=row, column=col, sticky="ew", padx=6, pady=6)
            form.grid_columnconfigure(col, weight=1)
            tk.Label(cell, text=label, bg=COLORS["background"], font=FONTS["label"]).pack(anchor="w")
            entry = ttk.Entry(cell, font=FONTS["entry"])
            entry.pack(fill="x")
            self.entries[key] = entry

        desc_cell = tk.Frame(form, bg=COLORS["background"])
        desc_cell.grid(row=2, column=0, columnspan=4, sticky="ew", padx=6, pady=6)
        tk.Label(desc_cell, text="Description", bg=COLORS["background"], font=FONTS["label"]).pack(
            anchor="w"
        )
        self.description_entry = ttk.Entry(desc_cell, font=FONTS["entry"])
        self.description_entry.pack(fill="x")

        btn_row = tk.Frame(self.root, bg=COLORS["background"])
        btn_row.pack(fill="x", padx=20, pady=10)
        ttk.Button(btn_row, text="Add Book", style="Success.TButton", command=self.add_book).pack(
            side="left", padx=4
        )
        ttk.Button(btn_row, text="Update Book", command=self.update_book).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Delete Book", style="Danger.TButton", command=self.delete_book).pack(
            side="left", padx=4
        )
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
        self.search_entry.bind("<Return>", lambda e: self.search_books())
        ttk.Button(search_row, text="Search", command=self.search_books).pack(side="left", padx=4)
        ttk.Button(
            search_row, text="Clear Search", style="Muted.TButton", command=self.load_books
        ).pack(side="left", padx=4)

        table_frame = tk.Frame(self.root, bg=COLORS["background"])
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings")
        for col, heading in zip(COLUMNS, HEADINGS):
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=110, anchor="center")
        self.tree.column("title", width=180, anchor="w")
        self.tree.column("author", width=140, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ------------------------------------------------------------ data
    def load_books(self):
        self.search_entry.delete(0, tk.END)
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
            self._populate(rows)
        except Exception:
            show_error("Unable to load books. Please try again.")
        finally:
            if conn:
                conn.close()

    def search_books(self):
        term = f"%{self.search_entry.get().strip()}%"
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? "
                "OR isbn LIKE ? OR category LIKE ? ORDER BY id DESC",
                (term, term, term, term),
            ).fetchall()
            self._populate(rows)
            if not rows:
                show_info("No books matched your search.", title="No Results")
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
                    row["id"], row["isbn"] or "", row["title"], row["author"],
                    row["category"] or "", row["quantity"], row["available"], row["shelf"] or "",
                ),
            )

    def _on_row_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.selected_id = None
            return
        values = self.tree.item(selection[0], "values")
        book_id = values[0]
        conn = None
        try:
            conn = connect_database()
            row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
            if row is None:
                return
            self.selected_id = row["id"]
            self.entries["isbn"].delete(0, tk.END)
            self.entries["isbn"].insert(0, row["isbn"] or "")
            self.entries["title"].delete(0, tk.END)
            self.entries["title"].insert(0, row["title"])
            self.entries["author"].delete(0, tk.END)
            self.entries["author"].insert(0, row["author"])
            self.entries["category"].delete(0, tk.END)
            self.entries["category"].insert(0, row["category"] or "")
            self.entries["publisher"].delete(0, tk.END)
            self.entries["publisher"].insert(0, row["publisher"] or "")
            self.entries["publication_year"].delete(0, tk.END)
            self.entries["publication_year"].insert(0, str(row["publication_year"] or ""))
            self.entries["quantity"].delete(0, tk.END)
            self.entries["quantity"].insert(0, str(row["quantity"]))
            self.entries["shelf"].delete(0, tk.END)
            self.entries["shelf"].insert(0, row["shelf"] or "")
            self.description_entry.delete(0, tk.END)
            self.description_entry.insert(0, row["description"] or "")
        except Exception:
            show_error("Unable to load the selected book.")
        finally:
            if conn:
                conn.close()

    def clear_form(self):
        self.selected_id = None
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    # --------------------------------------------------------- helpers
    def _read_form(self):
        return {
            "isbn": self.entries["isbn"].get().strip(),
            "title": self.entries["title"].get().strip(),
            "author": self.entries["author"].get().strip(),
            "category": self.entries["category"].get().strip(),
            "publisher": self.entries["publisher"].get().strip(),
            "publication_year": self.entries["publication_year"].get().strip(),
            "quantity": self.entries["quantity"].get().strip(),
            "shelf": self.entries["shelf"].get().strip(),
            "description": self.description_entry.get().strip(),
        }

    def _validate(self, data):
        if not not_empty(data["title"]):
            show_warning("Title cannot be empty.")
            return False
        if not not_empty(data["author"]):
            show_warning("Author cannot be empty.")
            return False
        if not is_valid_quantity(data["quantity"]):
            show_warning("Please enter a valid positive quantity.")
            return False
        if not is_valid_year(data["publication_year"]):
            show_warning("Please enter a valid publication year.")
            return False
        if not is_valid_isbn(data["isbn"]):
            show_warning("Please enter a valid ISBN (8-13 digits).")
            return False
        return True

    # --------------------------------------------------------- actions
    def add_book(self):
        data = self._read_form()
        if not self._validate(data):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()

            if data["isbn"]:
                existing = cur.execute(
                    "SELECT id FROM books WHERE isbn = ?", (data["isbn"],)
                ).fetchone()
                if existing:
                    show_warning("Book with this ISBN already exists.")
                    return

            quantity = int(data["quantity"])
            cur.execute(
                """INSERT INTO books
                   (isbn, title, author, category, publisher, publication_year,
                    quantity, available, shelf, description, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["isbn"] or None, data["title"], data["author"],
                    data["category"] or None, data["publisher"] or None,
                    int(data["publication_year"]) if data["publication_year"] else None,
                    quantity, quantity, data["shelf"] or None, data["description"] or None,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            show_info("Book added successfully.")
            self.clear_form()
            self.load_books()
        except Exception:
            show_error("Unable to add the book. Please try again.")
        finally:
            if conn:
                conn.close()

    def update_book(self):
        if self.selected_id is None:
            show_warning("Please select a book from the table to update.")
            return

        data = self._read_form()
        if not self._validate(data):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()

            if data["isbn"]:
                clash = cur.execute(
                    "SELECT id FROM books WHERE isbn = ? AND id != ?",
                    (data["isbn"], self.selected_id),
                ).fetchone()
                if clash:
                    show_warning("Book with this ISBN already exists.")
                    return

            current = cur.execute(
                "SELECT quantity, available FROM books WHERE id = ?", (self.selected_id,)
            ).fetchone()
            if current is None:
                show_error("Record not found.")
                return

            # Check currently issued copies to prevent setting quantity below active loans
            active_issued = cur.execute(
                "SELECT COUNT(*) AS n FROM issued_books WHERE book_id = ? AND status = 'Issued'",
                (self.selected_id,),
            ).fetchone()["n"]

            new_quantity = int(data["quantity"])
            if new_quantity < active_issued:
                show_warning(f"Quantity cannot be less than currently issued copies ({active_issued}).")
                return

            diff = new_quantity - current["quantity"]
            new_available = max(0, min(new_quantity, current["available"] + diff))

            cur.execute(
                """UPDATE books SET isbn=?, title=?, author=?, category=?, publisher=?,
                   publication_year=?, quantity=?, available=?, shelf=?, description=?
                   WHERE id=?""",
                (
                    data["isbn"] or None, data["title"], data["author"],
                    data["category"] or None, data["publisher"] or None,
                    int(data["publication_year"]) if data["publication_year"] else None,
                    new_quantity, new_available, data["shelf"] or None,
                    data["description"] or None, self.selected_id,
                ),
            )
            conn.commit()
            show_info("Book updated successfully.")
            self.clear_form()
            self.load_books()
        except Exception:
            show_error("Unable to update the book. Please try again.")
        finally:
            if conn:
                conn.close()

    def delete_book(self):
        if self.selected_id is None:
            show_warning("Please select a book from the table to delete.")
            return

        if not confirm("Are you sure you want to delete this book? This will also remove any past loan records for this book."):
            return

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            active = cur.execute(
                "SELECT COUNT(*) AS n FROM issued_books WHERE book_id = ? AND status = 'Issued'",
                (self.selected_id,),
            ).fetchone()["n"]

            if active > 0:
                show_warning("This book cannot be deleted because it is currently issued.")
                return

            # Delete past returned issue records first to ensure foreign key safety
            cur.execute("DELETE FROM issued_books WHERE book_id = ?", (self.selected_id,))
            cur.execute("DELETE FROM books WHERE id = ?", (self.selected_id,))
            conn.commit()
            show_info("Book deleted successfully.")
            self.clear_form()
            self.load_books()
        except Exception:
            show_error("Unable to delete the book. Please try again.")
        finally:
            if conn:
                conn.close()

    def _close(self):
        if self.on_close:
            self.on_close()
        self.root.destroy()
