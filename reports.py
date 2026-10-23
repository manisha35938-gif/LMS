"""
reports.py
-----------
Reporting window: summary statistics, overdue books, most-issued books,
active members and full issue history with date filtering and CSV export.
"""

import csv
import tkinter as tk
from tkinter import ttk, filedialog

from database import connect_database
from style import setup_style, COLORS, FONTS
from utils import (
    center_window, show_error, show_info, show_warning,
    clear_treeview, today_str, is_valid_date, days_overdue,
)


class ReportsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Reports")
        center_window(self.root, 1050, 680)
        setup_style(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()
        self.show_summary()

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        top_bar = tk.Frame(self.root, bg=COLORS["background"])
        top_bar.pack(fill="x", padx=20, pady=(15, 0))
        ttk.Button(
            top_bar, text="⬅ Back to Dashboard", style="Muted.TButton", command=self._close
        ).pack(anchor="w")

        tk.Label(
            self.root, text="Library Reports", bg=COLORS["background"],
            fg=COLORS["primary"], font=FONTS["heading"],
        ).pack(anchor="w", padx=20, pady=(10, 5))

        top_row = tk.Frame(self.root, bg=COLORS["background"])
        top_row.pack(fill="x", padx=20)

        self.report_choice = ttk.Combobox(
            top_row,
            state="readonly",
            width=28,
            values=[
                "Summary",
                "Overdue Books",
                "Most Issued Books",
                "Active Members",
                "Issue History",
            ],
        )
        self.report_choice.set("Summary")
        self.report_choice.pack(side="left")
        ttk.Button(top_row, text="Generate Report", command=self.generate).pack(side="left", padx=8)
        ttk.Button(
            top_row, text="Export to CSV", style="Success.TButton", command=self.export_csv
        ).pack(side="left", padx=8)

        date_row = tk.Frame(self.root, bg=COLORS["background"])
        date_row.pack(fill="x", padx=20, pady=8)
        tk.Label(date_row, text="From Date (YYYY-MM-DD):", bg=COLORS["background"], font=FONTS["label"]).pack(
            side="left"
        )
        self.from_date_entry = ttk.Entry(date_row, width=14)
        self.from_date_entry.pack(side="left", padx=6)
        tk.Label(date_row, text="To Date (YYYY-MM-DD):", bg=COLORS["background"], font=FONTS["label"]).pack(
            side="left", padx=(15, 0)
        )
        self.to_date_entry = ttk.Entry(date_row, width=14)
        self.to_date_entry.pack(side="left", padx=6)
        tk.Label(
            date_row, text="(applies to Issue History only, optional)",
            bg=COLORS["background"], fg=COLORS["muted"], font=FONTS["small"],
        ).pack(side="left", padx=6)

        table_frame = tk.Frame(self.root, bg=COLORS["background"])
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(table_frame, show="headings")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------------------------------------------------- helpers
    def _set_columns(self, columns, headings, widths=None):
        self.tree["columns"] = columns
        for i, (col, heading) in enumerate(zip(columns, headings)):
            self.tree.heading(col, text=heading)
            width = widths[i] if widths else 120
            self.tree.column(col, width=width, anchor="center")
        clear_treeview(self.tree)

    def generate(self):
        choice = self.report_choice.get()
        try:
            if choice == "Summary":
                self.show_summary()
            elif choice == "Overdue Books":
                self.show_overdue()
            elif choice == "Most Issued Books":
                self.show_most_issued()
            elif choice == "Active Members":
                self.show_active_members()
            elif choice == "Issue History":
                self.show_issue_history()
        except Exception:
            show_error("Unable to generate the report. Please try again.")

    # ------------------------------------------------------------ reports
    def show_summary(self):
        self._set_columns(("metric", "value"), ("Metric", "Value"), (300, 150))
        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()

            fines_total = cur.execute("SELECT COALESCE(SUM(fine), 0) AS n FROM issued_books WHERE status='Returned'").fetchone()["n"]

            metrics = [
                ("Total Books (titles)", cur.execute("SELECT COUNT(*) n FROM books").fetchone()["n"]),
                ("Total Book Copies", cur.execute("SELECT COALESCE(SUM(quantity),0) n FROM books").fetchone()["n"]),
                ("Available Copies", cur.execute("SELECT COALESCE(SUM(available),0) n FROM books").fetchone()["n"]),
                ("Currently Issued", cur.execute("SELECT COUNT(*) n FROM issued_books WHERE status='Issued'").fetchone()["n"]),
                ("Returned (all time)", cur.execute("SELECT COUNT(*) n FROM issued_books WHERE status='Returned'").fetchone()["n"]),
                ("Total Members", cur.execute("SELECT COUNT(*) n FROM members").fetchone()["n"]),
                (
                    "Overdue Books",
                    cur.execute(
                        "SELECT COUNT(*) n FROM issued_books WHERE status='Issued' AND due_date < ?",
                        (today_str(),),
                    ).fetchone()["n"],
                ),
                ("Total Fines Collected", f"₹{fines_total:.2f}"),
            ]
            for metric, value in metrics:
                self.tree.insert("", "end", values=(metric, value))
        except Exception:
            show_error("Unable to load summary report.")
        finally:
            if conn:
                conn.close()

    def show_overdue(self):
        self._set_columns(
            ("id", "book", "member", "issue_date", "due_date", "days_overdue"),
            ("Issue ID", "Book", "Member", "Issue Date", "Due Date", "Days Overdue"),
            (70, 220, 160, 100, 100, 110),
        )
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                """SELECT ib.id, b.title AS book, m.name AS member, ib.issue_date, ib.due_date
                   FROM issued_books ib
                   JOIN books b ON b.id = ib.book_id
                   JOIN members m ON m.id = ib.member_id
                   WHERE ib.status = 'Issued' AND ib.due_date < ?
                   ORDER BY ib.due_date ASC""",
                (today_str(),),
            ).fetchall()

            for row in rows:
                overdue = days_overdue(row["due_date"])
                self.tree.insert(
                    "", "end",
                    values=(row["id"], row["book"], row["member"], row["issue_date"], row["due_date"], overdue),
                )
            if not rows:
                show_info("No overdue books.", title="Overdue Books")
        except Exception:
            show_error("Unable to load overdue report.")
        finally:
            if conn:
                conn.close()

    def show_most_issued(self):
        self._set_columns(
            ("book", "times_issued"), ("Book Title", "Times Issued"), (400, 150)
        )
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                """SELECT b.title AS book, COUNT(*) AS times_issued
                   FROM issued_books ib JOIN books b ON b.id = ib.book_id
                   GROUP BY ib.book_id ORDER BY times_issued DESC LIMIT 10"""
            ).fetchall()
            for row in rows:
                self.tree.insert("", "end", values=(row["book"], row["times_issued"]))
            if not rows:
                show_info("No issue records yet.", title="Most Issued Books")
        except Exception:
            show_error("Unable to load most-issued report.")
        finally:
            if conn:
                conn.close()

    def show_active_members(self):
        self._set_columns(
            ("member", "phone", "books_held"), ("Member", "Phone", "Books Currently Held"), (250, 150, 160)
        )
        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(
                """SELECT m.name AS member, m.phone AS phone, COUNT(ib.id) AS books_held
                   FROM members m JOIN issued_books ib ON ib.member_id = m.id AND ib.status='Issued'
                   GROUP BY m.id ORDER BY books_held DESC"""
            ).fetchall()
            for row in rows:
                self.tree.insert("", "end", values=(row["member"], row["phone"] or "", row["books_held"]))
            if not rows:
                show_info("No members currently hold a book.", title="Active Members")
        except Exception:
            show_error("Unable to load active members report.")
        finally:
            if conn:
                conn.close()

    def show_issue_history(self):
        self._set_columns(
            ("id", "book", "member", "issue_date", "due_date", "return_date", "status", "fine"),
            ("Issue ID", "Book", "Member", "Issue Date", "Due Date", "Return Date", "Status", "Fine"),
            (70, 180, 140, 100, 100, 100, 90, 70),
        )

        from_date = self.from_date_entry.get().strip()
        to_date = self.to_date_entry.get().strip()
        if from_date and not is_valid_date(from_date):
            show_warning("Please enter a valid From Date (YYYY-MM-DD).")
            return
        if to_date and not is_valid_date(to_date):
            show_warning("Please enter a valid To Date (YYYY-MM-DD).")
            return

        query = """SELECT ib.id, b.title AS book, m.name AS member, ib.issue_date,
                          ib.due_date, ib.return_date, ib.status, ib.fine
                   FROM issued_books ib
                   JOIN books b ON b.id = ib.book_id
                   JOIN members m ON m.id = ib.member_id
                   WHERE 1=1"""
        params = []
        if from_date:
            query += " AND ib.issue_date >= ?"
            params.append(from_date)
        if to_date:
            query += " AND ib.issue_date <= ?"
            params.append(to_date)
        query += " ORDER BY ib.id DESC"

        conn = None
        try:
            conn = connect_database()
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                fine_val = f"₹{row['fine']:.2f}" if row["fine"] else "₹0.00"
                self.tree.insert(
                    "", "end",
                    values=(
                        row["id"], row["book"], row["member"], row["issue_date"],
                        row["due_date"], row["return_date"] or "-", row["status"], fine_val,
                    ),
                )
            if not rows:
                show_info("No records found for the selected range.", title="Issue History")
        except Exception:
            show_error("Unable to load issue history report.")
        finally:
            if conn:
                conn.close()

    # ------------------------------------------------------------ export
    def export_csv(self):
        columns = self.tree["columns"]
        if not columns or not self.tree.get_children():
            show_warning("There is no report data to export. Generate a report first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="library_report.csv",
            title="Export Report",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([self.tree.heading(col)["text"] for col in columns])
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item, "values"))
            show_info(f"Report exported successfully to:\n{file_path}")
        except Exception:
            show_error("Unable to export the report. Please check the file location and try again.")

    def _close(self):
        self.root.destroy()
