"""Professional dashboard for the Library Management System."""
import tkinter as tk
from tkinter import ttk, messagebox

from database.database import connect_database
from style import setup_style, COLORS, FONTS
from utils import center_window, confirm, today_str


class DashboardWindow:
    def __init__(self, root, current_user="admin"):
        self.root = root
        self.current_user = current_user
        self.root.title("Library Management System | Dashboard")
        center_window(self.root, 1180, 760)
        self.root.minsize(980, 650)
        setup_style(self.root)
        self.stat_labels = {}
        self._build_ui()
        self.refresh_stats()
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def _build_ui(self):
        self.sidebar = tk.Frame(self.root, bg=COLORS["primary"], width=218)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="📚", bg=COLORS["primary"], fg="white", font=("Segoe UI", 32)).pack(pady=(25, 0))
        tk.Label(self.sidebar, text="LIBRARY SYSTEM", bg=COLORS["primary"], fg="white", font=("Segoe UI", 13, "bold")).pack(pady=(2, 6))
        tk.Label(self.sidebar, text=f"User: {self.current_user}", bg=COLORS["primary"], fg="#aed6f1", font=FONTS["small"]).pack(pady=(0, 16))
        tk.Frame(self.sidebar, bg="#ffffff", height=1).pack(fill="x", padx=18, pady=(0, 15))
        items = [
            ("▦   Dashboard", self.refresh_stats),
            ("▤   Manage Books", self.open_books),
            ("♙   Manage Members", self.open_members),
            ("⇄   Issue / Return", self.open_issue_return),
            ("▥   Reports", self.open_reports),
            ("↻   Refresh Data", self.refresh_stats),
            ("⚙   Change Password", self.open_change_password),
        ]
        for label, action in items:
            btn = tk.Button(self.sidebar, text=label, command=action, bg=COLORS["primary"], fg="white",
                            activebackground=COLORS["primary_dark"], activeforeground="white", bd=0,
                            anchor="w", padx=20, pady=13, font=FONTS["label_bold"], cursor="hand2")
            btn.pack(fill="x", padx=7, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORS["primary_dark"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=COLORS["primary"]))
        tk.Frame(self.sidebar, bg="#ffffff", height=1).pack(fill="x", padx=18, pady=(18, 12))
        tk.Button(self.sidebar, text="↪   Logout", command=self.logout, bg="#a93226", fg="white",
                  activebackground="#922b21", activeforeground="white", bd=0, anchor="w",
                  padx=20, pady=12, font=FONTS["label_bold"], cursor="hand2").pack(fill="x", padx=7)
        tk.Label(self.sidebar, text="Library Management System\nDesktop Application", bg=COLORS["primary"],
                 fg="#d6eaf8", font=FONTS["small"], justify="left").pack(side="bottom", anchor="w", padx=18, pady=18)

        main = tk.Frame(self.root, bg=COLORS["background"])
        main.pack(side="left", fill="both", expand=True)
        header = tk.Frame(main, bg=COLORS["background"])
        header.pack(fill="x", padx=28, pady=(24, 8))
        tk.Label(header, text="Dashboard Overview", bg=COLORS["background"], fg=COLORS["primary"],
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(header, text=f"Today  |  {today_str()}", bg=COLORS["background"], fg=COLORS["muted"],
                 font=FONTS["label"]).pack(side="right", pady=8)
        tk.Label(main, text="Here is a quick summary of your library activity.", bg=COLORS["background"],
                 fg=COLORS["muted"], font=FONTS["label"]).pack(anchor="w", padx=30, pady=(0, 12))

        cards = tk.Frame(main, bg=COLORS["background"])
        cards.pack(fill="x", padx=20, pady=(0, 15))
        card_specs = [
            ("total_books", "Total Book Copies", "#2471a3", "📚"),
            ("available_books", "Available Copies", "#239b56", "✓"),
            ("issued_books", "Currently Issued", "#d68910", "⇄"),
            ("total_members", "Registered Members", "#7d3c98", "♙"),
            ("overdue_books", "Overdue Books", "#c0392b", "!"),
        ]
        for key, label, color, symbol in card_specs:
            self._make_card(cards, key, label, color, symbol)

        actions = tk.Frame(main, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        actions.pack(fill="x", padx=28, pady=(0, 16))
        tk.Label(actions, text="Quick Actions", bg=COLORS["surface"], fg=COLORS["primary"],
                 font=FONTS["heading"]).pack(anchor="w", padx=16, pady=(12, 8))
        action_row = tk.Frame(actions, bg=COLORS["surface"])
        action_row.pack(fill="x", padx=10, pady=(0, 12))
        for label, command, style in [
            ("＋  Add / Manage Books", self.open_books, "TButton"),
            ("＋  Manage Members", self.open_members, "TButton"),
            ("⇄  Issue or Return Book", self.open_issue_return, "Success.TButton"),
            ("▥  View Reports", self.open_reports, "Muted.TButton"),
        ]:
            ttk.Button(action_row, text=label, command=command, style=style).pack(side="left", expand=True, fill="x", padx=5, ipady=5)

        lower = tk.Frame(main, bg=COLORS["background"])
        lower.pack(fill="both", expand=True, padx=28, pady=(0, 22))
        recent_panel = tk.Frame(lower, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        recent_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(recent_panel, text="Recent Issue / Return Activity", bg=COLORS["surface"], fg=COLORS["primary"],
                 font=FONTS["heading"]).pack(anchor="w", padx=14, pady=(12, 8))
        columns = ("book", "member", "issued", "due", "status")
        self.recent_table = ttk.Treeview(recent_panel, columns=columns, show="headings", height=7)
        for col, title, width in [("book", "Book", 155), ("member", "Member", 115), ("issued", "Issue Date", 85), ("due", "Due Date", 85), ("status", "Status", 75)]:
            self.recent_table.heading(col, text=title)
            self.recent_table.column(col, width=width, minwidth=60, anchor="w")
        self.recent_table.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        stock_panel = tk.Frame(lower, bg=COLORS["surface"], width=260, highlightbackground=COLORS["border"], highlightthickness=1)
        stock_panel.pack(side="right", fill="y", padx=(8, 0))
        stock_panel.pack_propagate(False)
        tk.Label(stock_panel, text="Low Stock Alert", bg=COLORS["surface"], fg=COLORS["primary"],
                 font=FONTS["heading"]).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(stock_panel, text="Books with 2 or fewer available copies", bg=COLORS["surface"], fg=COLORS["muted"],
                 font=FONTS["small"], wraplength=225, justify="left").pack(anchor="w", padx=14, pady=(0, 8))
        self.low_stock_list = tk.Listbox(stock_panel, height=8, bd=0, highlightthickness=0,
                                         bg=COLORS["surface"], fg=COLORS["text"], font=FONTS["label"], activestyle="none")
        self.low_stock_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _make_card(self, parent, key, label, color, symbol):
        card = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(side="left", expand=True, fill="both", padx=7, ipady=5)
        tk.Frame(card, bg=color, height=4).pack(fill="x")
        tk.Label(card, text=symbol, bg=COLORS["surface"], fg=color, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=12, pady=(8, 0))
        value = tk.Label(card, text="—", bg=COLORS["surface"], fg=COLORS["text"], font=("Segoe UI", 23, "bold"))
        value.pack(anchor="w", padx=12, pady=(1, 0))
        tk.Label(card, text=label, bg=COLORS["surface"], fg=COLORS["muted"], font=FONTS["small"], wraplength=150).pack(anchor="w", padx=12, pady=(0, 10))
        self.stat_labels[key] = value

    def refresh_stats(self):
        if not self.stat_labels:
            return
        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            queries = {
                "total_books": "SELECT COALESCE(SUM(quantity), 0) AS n FROM books",
                "available_books": "SELECT COALESCE(SUM(available), 0) AS n FROM books",
                "issued_books": "SELECT COUNT(*) AS n FROM issued_books WHERE status = 'Issued'",
                "total_members": "SELECT COUNT(*) AS n FROM members",
            }
            values = {}
            for key, sql in queries.items():
                cur.execute(sql)
                values[key] = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status = 'Issued' AND due_date < ?", (today_str(),))
            values["overdue_books"] = cur.fetchone()["n"]
            for key, value in values.items():
                self.stat_labels[key].config(text=str(value))

            cur.execute("""SELECT b.title, m.name, i.issue_date, i.due_date, i.status
                           FROM issued_books i JOIN books b ON b.id=i.book_id
                           JOIN members m ON m.id=i.member_id
                           ORDER BY i.id DESC LIMIT 12""")
            rows = cur.fetchall()
            for item in self.recent_table.get_children():
                self.recent_table.delete(item)
            for row in rows:
                self.recent_table.insert("", "end", values=(row["title"], row["name"], row["issue_date"], row["due_date"], row["status"]))

            cur.execute("SELECT title, available FROM books WHERE available <= 2 ORDER BY available ASC, title COLLATE NOCASE LIMIT 20")
            low_stock = cur.fetchall()
            self.low_stock_list.delete(0, tk.END)
            if not low_stock:
                self.low_stock_list.insert(tk.END, "✓ No low-stock books")
            else:
                for row in low_stock:
                    self.low_stock_list.insert(tk.END, f"{row['title']}  ·  {row['available']} left")
        except Exception as exc:
            for label in self.stat_labels.values():
                label.config(text="—")
            messagebox.showerror("Dashboard Error", f"Could not load dashboard data.\n\n{exc}", parent=self.root)
        finally:
            if conn is not None:
                conn.close()

    def open_books(self):
        import books
        books.BooksWindow(tk.Toplevel(self.root), on_close=self.refresh_stats)

    def open_members(self):
        import members
        members.MembersWindow(tk.Toplevel(self.root), on_close=self.refresh_stats)

    def open_issue_return(self):
        import issue_return
        issue_return.IssueReturnWindow(tk.Toplevel(self.root), on_close=self.refresh_stats)

    def open_reports(self):
        import reports
        reports.ReportsWindow(tk.Toplevel(self.root))

    def open_change_password(self):
        import change_password
        change_password.ChangePasswordWindow(tk.Toplevel(self.root), current_user=self.current_user)

    def logout(self):
        if confirm("Are you sure you want to logout?", title="Logout"):
            self.root.destroy()
            import login
            login_root = tk.Tk()
            login.LoginWindow(login_root)
            login_root.mainloop()

    def exit_app(self):
        if confirm("Are you sure you want to exit the application?", title="Exit"):
            self.root.destroy()
