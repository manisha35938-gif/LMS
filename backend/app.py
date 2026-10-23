"""
backend/app.py
--------------
Core Flask web application implementing the complete Library Management System (LMS).
Handles authentication, routes, transactional loan operations, and reporting.
"""

import os
import csv
import io
from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, Response
)

from database.database import connect_database, init_database
from backend.security import hash_password, verify_password
from backend.validators import (
    not_empty, is_valid_phone, is_valid_email,
    is_valid_quantity, is_valid_year, is_valid_isbn
)
from backend.utils import (
    today_str, add_days_str, is_valid_date,
    calculate_fine, days_overdue, format_currency,
    LOAN_PERIOD_DAYS
)

# Initialize Flask application with explicit template and static paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "lms-secret-key-production-2026")

# Context processor for templates
@app.context_processor
def inject_globals():
    return {
        "current_user": session.get("username"),
        "today_str": today_str(),
        "format_currency": format_currency,
        "loan_period_days": LOAN_PERIOD_DAYS
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# Ensure database tables exist at startup
with app.app_context():
    try:
        init_database()
    except Exception as e:
        print(f"Database initialization notice: {e}")


# ------------------------------------------------------------- Auth Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template("login.html")

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = cur.fetchone()

            if user is None or not verify_password(password, user["password_hash"]):
                flash("Invalid username or password.", "danger")
                return render_template("login.html")

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash("Unable to connect to the database. Please try again.", "danger")
        finally:
            if conn:
                conn.close()

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


# ------------------------------------------------------------- Dashboard
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        stats = {
            "total_books": cur.execute("SELECT COALESCE(SUM(quantity), 0) AS n FROM books").fetchone()["n"],
            "available_books": cur.execute("SELECT COALESCE(SUM(available), 0) AS n FROM books").fetchone()["n"],
            "issued_books": cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status = 'Issued'").fetchone()["n"],
            "total_members": cur.execute("SELECT COUNT(*) AS n FROM members").fetchone()["n"],
            "overdue_books": cur.execute(
                "SELECT COUNT(*) AS n FROM issued_books WHERE status = 'Issued' AND due_date < ?",
                (today_str(),)
            ).fetchone()["n"],
        }

        # Recent activities (last 10)
        recent_activity = [dict(r) for r in cur.execute("""
            SELECT ib.id, b.title AS book_title, m.name AS member_name,
                   ib.issue_date, ib.due_date, ib.status
            FROM issued_books ib
            JOIN books b ON b.id = ib.book_id
            JOIN members m ON m.id = ib.member_id
            ORDER BY ib.id DESC LIMIT 10
        """).fetchall()]

        # Low stock alert (<= 2 copies available)
        low_stock = [dict(r) for r in cur.execute("""
            SELECT id, title, author, available, quantity
            FROM books
            WHERE available <= 2
            ORDER BY available ASC, title ASC LIMIT 10
        """).fetchall()]

        return render_template(
            "dashboard.html",
            stats=stats,
            recent_activity=recent_activity,
            low_stock=low_stock
        )
    except Exception as e:
        flash(f"Error loading dashboard: {e}", "danger")
        return render_template("dashboard.html", stats={}, recent_activity=[], low_stock=[])
    finally:
        if conn:
            conn.close()


# ------------------------------------------------------------- Books
@app.route("/books")
@login_required
def books():
    search_query = request.args.get("q", "").strip()
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()
        if search_query:
            term = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM books
                WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
                ORDER BY id DESC
            """, (term, term, term, term))
        else:
            cur.execute("SELECT * FROM books ORDER BY id DESC")
        book_list = [dict(row) for row in cur.fetchall()]
        return render_template("books.html", books=book_list, search_query=search_query)
    finally:
        if conn:
            conn.close()


@app.route("/books/add", methods=["POST"])
@login_required
def add_book():
    isbn = request.form.get("isbn", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    category = request.form.get("category", "").strip()
    publisher = request.form.get("publisher", "").strip()
    year = request.form.get("publication_year", "").strip()
    quantity_str = request.form.get("quantity", "1").strip()
    shelf = request.form.get("shelf", "").strip()
    description = request.form.get("description", "").strip()

    if not not_empty(title):
        flash("Book title cannot be empty.", "warning")
        return redirect(url_for("books"))
    if not not_empty(author):
        flash("Author cannot be empty.", "warning")
        return redirect(url_for("books"))
    if not is_valid_quantity(quantity_str):
        flash("Please enter a valid positive quantity.", "warning")
        return redirect(url_for("books"))
    if not is_valid_year(year):
        flash("Please enter a valid publication year.", "warning")
        return redirect(url_for("books"))
    if not is_valid_isbn(isbn):
        flash("Please enter a valid ISBN (8-13 digits).", "warning")
        return redirect(url_for("books"))

    quantity = int(quantity_str)
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()
        if isbn:
            clash = cur.execute("SELECT id FROM books WHERE isbn = ?", (isbn,)).fetchone()
            if clash:
                flash("A book with this ISBN already exists.", "warning")
                return redirect(url_for("books"))

        cur.execute("""
            INSERT INTO books (isbn, title, author, category, publisher, publication_year,
                               quantity, available, shelf, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            isbn or None, title, author, category or None, publisher or None,
            int(year) if year else None, quantity, quantity, shelf or None,
            description or None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        flash("Book added successfully!", "success")
    except Exception as e:
        flash(f"Error adding book: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("books"))


@app.route("/books/edit/<int:book_id>", methods=["POST"])
@login_required
def edit_book(book_id):
    isbn = request.form.get("isbn", "").strip()
    title = request.form.get("title", "").strip()
    author = request.form.get("author", "").strip()
    category = request.form.get("category", "").strip()
    publisher = request.form.get("publisher", "").strip()
    year = request.form.get("publication_year", "").strip()
    quantity_str = request.form.get("quantity", "1").strip()
    shelf = request.form.get("shelf", "").strip()
    description = request.form.get("description", "").strip()

    if not not_empty(title) or not not_empty(author):
        flash("Title and Author are required.", "warning")
        return redirect(url_for("books"))
    if not is_valid_quantity(quantity_str):
        flash("Please enter a valid positive quantity.", "warning")
        return redirect(url_for("books"))

    new_quantity = int(quantity_str)
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        if isbn:
            clash = cur.execute(
                "SELECT id FROM books WHERE isbn = ? AND id != ?", (isbn, book_id)
            ).fetchone()
            if clash:
                flash("Another book with this ISBN already exists.", "warning")
                return redirect(url_for("books"))

        current = cur.execute("SELECT quantity, available FROM books WHERE id = ?", (book_id,)).fetchone()
        if not current:
            flash("Book record not found.", "danger")
            return redirect(url_for("books"))

        active_loans = cur.execute(
            "SELECT COUNT(*) AS n FROM issued_books WHERE book_id = ? AND status = 'Issued'",
            (book_id,)
        ).fetchone()["n"]

        if new_quantity < active_loans:
            flash(f"Quantity cannot be less than currently issued copies ({active_loans}).", "warning")
            return redirect(url_for("books"))

        diff = new_quantity - current["quantity"]
        new_available = max(0, min(new_quantity, current["available"] + diff))

        cur.execute("""
            UPDATE books SET isbn=?, title=?, author=?, category=?, publisher=?,
                             publication_year=?, quantity=?, available=?, shelf=?, description=?
            WHERE id=?
        """, (
            isbn or None, title, author, category or None, publisher or None,
            int(year) if year else None, new_quantity, new_available, shelf or None,
            description or None, book_id
        ))
        conn.commit()
        flash("Book updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating book: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("books"))


@app.route("/books/delete/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        active = cur.execute(
            "SELECT COUNT(*) AS n FROM issued_books WHERE book_id = ? AND status = 'Issued'",
            (book_id,)
        ).fetchone()["n"]
        if active > 0:
            flash("This book cannot be deleted because it is currently issued to a member.", "warning")
            return redirect(url_for("books"))

        cur.execute("DELETE FROM issued_books WHERE book_id = ?", (book_id,))
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        flash("Book deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting book: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("books"))


# ------------------------------------------------------------- Members
@app.route("/members")
@login_required
def members():
    search_query = request.args.get("q", "").strip()
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()
        if search_query:
            term = f"%{search_query}%"
            cur.execute("""
                SELECT * FROM members
                WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                ORDER BY id DESC
            """, (term, term, term))
        else:
            cur.execute("SELECT * FROM members ORDER BY id DESC")
        member_list = [dict(row) for row in cur.fetchall()]
        return render_template("members.html", members=member_list, search_query=search_query)
    finally:
        if conn:
            conn.close()


@app.route("/members/add", methods=["POST"])
@login_required
def add_member():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    status = request.form.get("status", "Active").strip()

    if not not_empty(name):
        flash("Member name cannot be empty.", "warning")
        return redirect(url_for("members"))
    if phone and not is_valid_phone(phone):
        flash("Please enter a valid phone number (7-15 digits).", "warning")
        return redirect(url_for("members"))
    if not is_valid_email(email):
        flash("Please enter a valid email address.", "warning")
        return redirect(url_for("members"))

    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        if phone:
            clash = cur.execute("SELECT id FROM members WHERE phone = ?", (phone,)).fetchone()
            if clash:
                flash("A member with this phone number already exists.", "warning")
                return redirect(url_for("members"))
        if email:
            clash = cur.execute("SELECT id FROM members WHERE email = ?", (email,)).fetchone()
            if clash:
                flash("A member with this email address already exists.", "warning")
                return redirect(url_for("members"))

        cur.execute("""
            INSERT INTO members (name, phone, email, address, registration_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone or None, email or None, address or None, today_str(), status))
        conn.commit()
        flash("Member registered successfully!", "success")
    except Exception as e:
        flash(f"Error registering member: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("members"))


@app.route("/members/edit/<int:member_id>", methods=["POST"])
@login_required
def edit_member(member_id):
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    status = request.form.get("status", "Active").strip()

    if not not_empty(name):
        flash("Member name cannot be empty.", "warning")
        return redirect(url_for("members"))
    if phone and not is_valid_phone(phone):
        flash("Please enter a valid phone number.", "warning")
        return redirect(url_for("members"))
    if not is_valid_email(email):
        flash("Please enter a valid email address.", "warning")
        return redirect(url_for("members"))

    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        if phone:
            clash = cur.execute(
                "SELECT id FROM members WHERE phone = ? AND id != ?", (phone, member_id)
            ).fetchone()
            if clash:
                flash("Another member with this phone already exists.", "warning")
                return redirect(url_for("members"))
        if email:
            clash = cur.execute(
                "SELECT id FROM members WHERE email = ? AND id != ?", (email, member_id)
            ).fetchone()
            if clash:
                flash("Another member with this email already exists.", "warning")
                return redirect(url_for("members"))

        cur.execute("""
            UPDATE members SET name=?, phone=?, email=?, address=?, status=? WHERE id=?
        """, (name, phone or None, email or None, address or None, status, member_id))
        conn.commit()
        flash("Member updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating member: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("members"))


@app.route("/members/delete/<int:member_id>", methods=["POST"])
@login_required
def delete_member(member_id):
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        active = cur.execute(
            "SELECT COUNT(*) AS n FROM issued_books WHERE member_id = ? AND status = 'Issued'",
            (member_id,)
        ).fetchone()["n"]
        if active > 0:
            flash("Member cannot be deleted because they currently have issued books.", "warning")
            return redirect(url_for("members"))

        cur.execute("DELETE FROM issued_books WHERE member_id = ?", (member_id,))
        cur.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        flash("Member deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting member: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("members"))


# ------------------------------------------------------------- Issue / Return
@app.route("/issue-return")
@login_required
def issue_return():
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        # Active loans
        active_loans = [dict(r) for r in cur.execute("""
            SELECT ib.id, b.title AS book_title, m.name AS member_name,
                   ib.issue_date, ib.due_date, ib.status, b.id AS book_id, m.id AS member_id
            FROM issued_books ib
            JOIN books b ON b.id = ib.book_id
            JOIN members m ON m.id = ib.member_id
            WHERE ib.status = 'Issued'
            ORDER BY ib.due_date ASC
        """).fetchall()]

        # Loan History
        loan_history = [dict(r) for r in cur.execute("""
            SELECT ib.id, b.title AS book_title, m.name AS member_name,
                   ib.issue_date, ib.due_date, ib.return_date, ib.status, ib.fine
            FROM issued_books ib
            JOIN books b ON b.id = ib.book_id
            JOIN members m ON m.id = ib.member_id
            ORDER BY ib.id DESC LIMIT 100
        """).fetchall()]

        # Members for dropdown
        members_list = [dict(r) for r in cur.execute(
            "SELECT id, name, phone FROM members WHERE status = 'Active' ORDER BY name ASC"
        ).fetchall()]

        # Books for dropdown
        available_books = [dict(r) for r in cur.execute(
            "SELECT id, title, available FROM books WHERE available > 0 ORDER BY title ASC"
        ).fetchall()]

        return render_template(
            "issue_return.html",
            active_loans=active_loans,
            loan_history=loan_history,
            members=members_list,
            books=available_books,
            default_due_date=add_days_str(LOAN_PERIOD_DAYS)
        )
    finally:
        if conn:
            conn.close()


@app.route("/issue", methods=["POST"])
@login_required
def issue_book():
    member_id = request.form.get("member_id", type=int)
    book_id = request.form.get("book_id", type=int)
    issue_date = request.form.get("issue_date", today_str()).strip()
    due_date = request.form.get("due_date", add_days_str(LOAN_PERIOD_DAYS)).strip()

    if not member_id or not book_id:
        flash("Please select both a member and a book.", "warning")
        return redirect(url_for("issue_return"))
    if not is_valid_date(issue_date) or not is_valid_date(due_date):
        flash("Please enter valid dates (YYYY-MM-DD).", "warning")
        return redirect(url_for("issue_return"))
    if due_date < issue_date:
        flash("Due date cannot be earlier than issue date.", "warning")
        return redirect(url_for("issue_return"))

    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        # Check availability
        book = cur.execute("SELECT available FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book or book["available"] <= 0:
            flash("Selected book is currently out of stock.", "warning")
            return redirect(url_for("issue_return"))

        # Prevent duplicate issue to same member
        already_issued = cur.execute(
            "SELECT id FROM issued_books WHERE book_id = ? AND member_id = ? AND status = 'Issued'",
            (book_id, member_id)
        ).fetchone()
        if already_issued:
            flash("This member already has an active loan for this book.", "warning")
            return redirect(url_for("issue_return"))

        cur.execute("""
            INSERT INTO issued_books (book_id, member_id, issue_date, due_date, status, fine)
            VALUES (?, ?, ?, ?, 'Issued', 0)
        """, (book_id, member_id, issue_date, due_date))
        cur.execute("UPDATE books SET available = available - 1 WHERE id = ?", (book_id,))
        conn.commit()
        flash("Book issued successfully!", "success")
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error issuing book: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("issue_return"))


@app.route("/return/<int:issue_id>", methods=["POST"])
@login_required
def return_book(issue_id):
    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        record = cur.execute("SELECT * FROM issued_books WHERE id = ?", (issue_id,)).fetchone()
        if not record or record["status"] == "Returned":
            flash("Loan record is either missing or already returned.", "warning")
            return redirect(url_for("issue_return"))

        return_date = today_str()
        fine = calculate_fine(record["due_date"], return_date)

        cur.execute("""
            UPDATE issued_books SET return_date = ?, status = 'Returned', fine = ? WHERE id = ?
        """, (return_date, fine, issue_id))
        cur.execute(
            "UPDATE books SET available = MIN(quantity, available + 1) WHERE id = ?",
            (record["book_id"],)
        )
        conn.commit()

        if fine > 0:
            flash(f"Book returned! Overdue fine charged: {format_currency(fine)}", "warning")
        else:
            flash("Book returned successfully with zero fine.", "success")
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error returning book: {e}", "danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("issue_return"))


# ------------------------------------------------------------- Reports
@app.route("/reports")
@login_required
def reports():
    report_type = request.args.get("type", "summary")
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        data = []
        headers = []

        if report_type == "summary":
            headers = ["Metric", "Value"]
            fines = cur.execute("SELECT COALESCE(SUM(fine), 0) AS n FROM issued_books WHERE status='Returned'").fetchone()["n"]
            data = [
                ("Total Book Titles", cur.execute("SELECT COUNT(*) AS n FROM books").fetchone()["n"]),
                ("Total Book Copies", cur.execute("SELECT COALESCE(SUM(quantity), 0) AS n FROM books").fetchone()["n"]),
                ("Available Copies", cur.execute("SELECT COALESCE(SUM(available), 0) AS n FROM books").fetchone()["n"]),
                ("Currently Issued", cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status='Issued'").fetchone()["n"]),
                ("Returned Loans", cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status='Returned'").fetchone()["n"]),
                ("Total Members", cur.execute("SELECT COUNT(*) AS n FROM members").fetchone()["n"]),
                ("Overdue Books", cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status='Issued' AND due_date < ?", (today_str(),)).fetchone()["n"]),
                ("Total Fines Collected", format_currency(fines)),
            ]
        elif report_type == "overdue":
            headers = ["Issue ID", "Book Title", "Member Name", "Issue Date", "Due Date", "Days Overdue"]
            rows = cur.execute("""
                SELECT ib.id, b.title, m.name, ib.issue_date, ib.due_date
                FROM issued_books ib
                JOIN books b ON b.id = ib.book_id
                JOIN members m ON m.id = ib.member_id
                WHERE ib.status = 'Issued' AND ib.due_date < ?
                ORDER BY ib.due_date ASC
            """, (today_str(),)).fetchall()
            for r in rows:
                data.append((r["id"], r["title"], r["name"], r["issue_date"], r["due_date"], days_overdue(r["due_date"])))
        elif report_type == "most_issued":
            headers = ["Book Title", "Author", "Times Issued"]
            rows = cur.execute("""
                SELECT b.title, b.author, COUNT(ib.id) AS times_issued
                FROM issued_books ib
                JOIN books b ON b.id = ib.book_id
                GROUP BY ib.book_id
                ORDER BY times_issued DESC LIMIT 15
            """).fetchall()
            for r in rows:
                data.append((r["title"], r["author"], r["times_issued"]))
        elif report_type == "active_members":
            headers = ["Member Name", "Phone", "Books Currently Held"]
            rows = cur.execute("""
                SELECT m.name, m.phone, COUNT(ib.id) AS books_held
                FROM members m
                JOIN issued_books ib ON ib.member_id = m.id AND ib.status='Issued'
                GROUP BY m.id
                ORDER BY books_held DESC
            """).fetchall()
            for r in rows:
                data.append((r["name"], r["phone"] or "-", r["books_held"]))
        elif report_type == "history":
            headers = ["Issue ID", "Book", "Member", "Issue Date", "Due Date", "Return Date", "Status", "Fine"]
            query = """
                SELECT ib.id, b.title, m.name, ib.issue_date, ib.due_date, ib.return_date, ib.status, ib.fine
                FROM issued_books ib
                JOIN books b ON b.id = ib.book_id
                JOIN members m ON m.id = ib.member_id
                WHERE 1=1
            """
            params = []
            if from_date:
                query += " AND ib.issue_date >= ?"
                params.append(from_date)
            if to_date:
                query += " AND ib.issue_date <= ?"
                params.append(to_date)
            query += " ORDER BY ib.id DESC LIMIT 200"
            rows = cur.execute(query, params).fetchall()
            for r in rows:
                data.append((r["id"], r["title"], r["name"], r["issue_date"], r["due_date"], r["return_date"] or "-", r["status"], format_currency(r["fine"])))

        return render_template(
            "reports.html",
            report_type=report_type,
            headers=headers,
            data=data,
            from_date=from_date,
            to_date=to_date
        )
    finally:
        if conn:
            conn.close()


@app.route("/reports/export")
@login_required
def export_csv():
    report_type = request.args.get("type", "summary")
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    conn = None
    try:
        conn = connect_database()
        cur = conn.cursor()

        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "summary":
            writer.writerow(["Metric", "Value"])
            fines = cur.execute("SELECT COALESCE(SUM(fine), 0) AS n FROM issued_books WHERE status='Returned'").fetchone()["n"]
            writer.writerow(["Total Books (titles)", cur.execute("SELECT COUNT(*) AS n FROM books").fetchone()["n"]])
            writer.writerow(["Total Book Copies", cur.execute("SELECT COALESCE(SUM(quantity), 0) AS n FROM books").fetchone()["n"]])
            writer.writerow(["Available Copies", cur.execute("SELECT COALESCE(SUM(available), 0) AS n FROM books").fetchone()["n"]])
            writer.writerow(["Currently Issued", cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status='Issued'").fetchone()["n"]])
            writer.writerow(["Returned Loans", cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status='Returned'").fetchone()["n"]])
            writer.writerow(["Total Members", cur.execute("SELECT COUNT(*) AS n FROM members").fetchone()["n"]])
            writer.writerow(["Overdue Books", cur.execute("SELECT COUNT(*) AS n FROM issued_books WHERE status='Issued' AND due_date < ?", (today_str(),)).fetchone()["n"]])
            writer.writerow(["Total Fines Collected", f"{fines:.2f}"])
        elif report_type == "overdue":
            writer.writerow(["Issue ID", "Book Title", "Member Name", "Issue Date", "Due Date", "Days Overdue"])
            rows = cur.execute("""
                SELECT ib.id, b.title, m.name, ib.issue_date, ib.due_date
                FROM issued_books ib
                JOIN books b ON b.id = ib.book_id
                JOIN members m ON m.id = ib.member_id
                WHERE ib.status = 'Issued' AND ib.due_date < ?
                ORDER BY ib.due_date ASC
            """, (today_str(),)).fetchall()
            for r in rows:
                writer.writerow([r["id"], r["title"], r["name"], r["issue_date"], r["due_date"], days_overdue(r["due_date"])])
        elif report_type == "most_issued":
            writer.writerow(["Book Title", "Author", "Times Issued"])
            rows = cur.execute("""
                SELECT b.title, b.author, COUNT(ib.id) AS times_issued
                FROM issued_books ib
                JOIN books b ON b.id = ib.book_id
                GROUP BY ib.book_id
                ORDER BY times_issued DESC
            """).fetchall()
            for r in rows:
                writer.writerow([r["title"], r["author"], r["times_issued"]])
        elif report_type == "active_members":
            writer.writerow(["Member Name", "Phone", "Books Currently Held"])
            rows = cur.execute("""
                SELECT m.name, m.phone, COUNT(ib.id) AS books_held
                FROM members m
                JOIN issued_books ib ON ib.member_id = m.id AND ib.status='Issued'
                GROUP BY m.id
                ORDER BY books_held DESC
            """).fetchall()
            for r in rows:
                writer.writerow([r["name"], r["phone"] or "", r["books_held"]])
        elif report_type == "history":
            writer.writerow(["Issue ID", "Book", "Member", "Issue Date", "Due Date", "Return Date", "Status", "Fine"])
            query = """
                SELECT ib.id, b.title, m.name, ib.issue_date, ib.due_date, ib.return_date, ib.status, ib.fine
                FROM issued_books ib
                JOIN books b ON b.id = ib.book_id
                JOIN members m ON m.id = ib.member_id
                WHERE 1=1
            """
            params = []
            if from_date:
                query += " AND ib.issue_date >= ?"
                params.append(from_date)
            if to_date:
                query += " AND ib.issue_date <= ?"
                params.append(to_date)
            query += " ORDER BY ib.id DESC"
            rows = cur.execute(query, params).fetchall()
            for r in rows:
                writer.writerow([r["id"], r["title"], r["name"], r["issue_date"], r["due_date"], r["return_date"] or "-", r["status"], r["fine"]])

        csv_content = output.getvalue()
        # Prepend UTF-8 BOM so Excel opens it with proper character encoding
        response = Response("\ufeff" + csv_content, mimetype="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=library_{report_type}_report.csv"
        return response
    finally:
        if conn:
            conn.close()


# ------------------------------------------------------------- Change Password
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password:
            flash("All password fields are required.", "warning")
            return render_template("change_password.html")
        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "warning")
            return render_template("change_password.html")
        if new_password != confirm_password:
            flash("New passwords do not match.", "warning")
            return render_template("change_password.html")

        conn = None
        try:
            conn = connect_database()
            cur = conn.cursor()
            user = cur.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

            if not user or not verify_password(current_password, user["password_hash"]):
                flash("Current password is incorrect.", "danger")
                return render_template("change_password.html")

            cur.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), user["id"])
            )
            conn.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Error changing password: {e}", "danger")
        finally:
            if conn:
                conn.close()

    return render_template("change_password.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
