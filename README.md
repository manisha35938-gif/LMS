# 📚 Library Management System

## 1. Project Description

A desktop **Library Management System** built with **Python, Tkinter/ttk, and SQLite** —
developed as a B.Tech Computer Science project. It replaces manual library
record-keeping with a centralized, computerized system for managing books,
members, issuing/returning, and reporting, with secure authentication and
consistent, transaction-safe data handling.

## 2. Features

- Secure login with hashed passwords (no plain text, ever)
- Dashboard with live statistics (Total Books, Available, Issued, Members, Overdue) — calculated from the database, never hard-coded
- **Books**: add / update / delete / search, duplicate-ISBN protection, quantity validation, blocks deletion of currently-issued books
- **Members**: add / update / delete / search, duplicate phone/email protection, blocks deletion of members with active loans
- **Issue / Return**: availability checks, transactional stock updates, duplicate-issue prevention, prevents double-return
- **Overdue & fines**: automatic overdue detection, configurable per-day fine calculation
- **Issue history**: searchable/filterable by member, book, status, date
- **Reports**: summary, overdue books, most-issued books, active members, date-filtered issue history
- **CSV export** for any generated report
- **Change password**: verifies current password, enforces minimum length, confirms match
- Confirmation dialogs before every destructive action (delete, logout)
- Input validation and graceful error handling on every screen — the app never crashes on a bad user input

## 3. Technologies

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| GUI | Tkinter / ttk |
| Database | SQLite3 |
| Password security | Werkzeug (`generate_password_hash` / `check_password_hash`) |

## 4. Requirements

- Python 3.8+
- Werkzeug (see `requirements.txt`) — Tkinter and sqlite3 ship with the standard Python installation and are not listed as dependencies.

## 5. Installation

```bash
pip install -r requirements.txt
```

## 6. How to Run

```bash
python main.py
```

`main.py` automatically initializes the database, creates all tables if they
don't exist, and creates the default admin account if no users exist yet.
You do **not** need to run `database.py` manually or set up anything by hand.

## 7. Default Login

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

> Change this after first login via **Sidebar → Change Password**. The old
> password stops working immediately once changed.

## 8. Database Information

SQLite database file: `library.db` (auto-created in the project folder on
first run). Foreign keys are enforced (`PRAGMA foreign_keys = ON`).

**`users`**
| Column | Type |
|---|---|
| id | INTEGER PK |
| username | TEXT UNIQUE NOT NULL |
| password_hash | TEXT NOT NULL |
| created_at | TEXT |

**`books`**
| Column | Type |
|---|---|
| id | INTEGER PK |
| isbn | TEXT UNIQUE |
| title | TEXT NOT NULL |
| author | TEXT NOT NULL |
| category | TEXT |
| publisher | TEXT |
| publication_year | INTEGER |
| quantity | INTEGER NOT NULL |
| available | INTEGER NOT NULL |
| shelf | TEXT |
| description | TEXT |
| created_at | TEXT |

**`members`**
| Column | Type |
|---|---|
| id | INTEGER PK |
| name | TEXT NOT NULL |
| phone | TEXT UNIQUE |
| email | TEXT UNIQUE |
| address | TEXT |
| registration_date | TEXT |
| status | TEXT DEFAULT 'Active' |

**`issued_books`**
| Column | Type |
|---|---|
| id | INTEGER PK |
| book_id | INTEGER NOT NULL → books.id |
| member_id | INTEGER NOT NULL → members.id |
| issue_date | TEXT NOT NULL |
| due_date | TEXT NOT NULL |
| return_date | TEXT |
| status | TEXT NOT NULL ('Issued' / 'Returned') |
| fine | REAL DEFAULT 0 |

This exact schema — same table names, same column names — is used
consistently by every module (`books.py`, `members.py`, `issue_return.py`,
`reports.py`, `dashboard.py`). There is no `issue_return` table (the module
is named that; the table is `issued_books`) and no `available_quantity`
column anywhere — only `available`.

## 9. Project Structure

```
LMS / (Library Management System)
│
├── .github/workflows/ci-cd.yml - GitHub Actions CI/CD automated test & build
├── main.py                    - application entry point (run this)
├── login.py                   - login screen
├── dashboard.py               - main hub, sidebar navigation, live statistics
├── database.py                - schema creation, connection helper, default admin
├── security.py                - password hashing (Werkzeug)
├── style.py                   - shared colors/fonts/ttk styling
├── utils.py                   - date helpers, message-box wrappers, constants
├── validators.py              - input validation helpers
├── books.py                   - book management module
├── members.py                 - member management module
├── issue_return.py            - issue / return / history module
├── reports.py                 - reports & CSV export
├── change_password.py         - change password screen
├── requirements.txt          - Python dependencies
├── start_library_system.bat   - Windows one-click launcher
├── push_to_github.bat         - One-click GitHub deployment script
├── build_exe.bat              - One-click standalone Windows .exe compiler
├── test_lms.py                - Automated unit & integration test suite
├── library.db                 - SQLite database (auto-created)
├── .gitignore                 - Git ignore configuration
└── README.md
```

## 10. How the Modules Communicate

- `main.py` calls `database.init_database()` once, then `login.main()`.
- `login.py` verifies credentials against `database.connect_database()` +
  `security.verify_password()`. On success it destroys its own window and
  opens `dashboard.DashboardWindow` in a new `Tk()` root.
- `dashboard.py` is the hub: each sidebar button opens the matching module
  (`books`, `members`, `issue_return`, `reports`, `change_password`) as a
  `Toplevel` window, and refreshes its own statistics when those windows close.
- Every feature module talks to the database directly through
  `database.connect_database()` — there is a single shared schema
  (Section 8) so no module ever disagrees with another about a table or
  column name.
- `security.py`, `style.py`, `utils.py` and `validators.py` are shared
  libraries imported by every window — password hashing, colors/fonts,
  date/message helpers, and input validation are each defined in exactly
  one place.
- Logging out destroys the dashboard window and re-opens `login.py`,
  completing the cycle.

## 11. Testing Checklist

All items below have been executed against the real application code
(not simulated) and pass:

**Authentication:** correct login · wrong password · wrong username · empty
username · empty password.

**Books:** add · update · delete · search · duplicate ISBN rejected ·
invalid quantity rejected · delete blocked while issued.

**Members:** add · update · delete · search · duplicate phone rejected ·
delete blocked while member has an active loan.

**Issue:** issue an available book · issuing an unavailable book is blocked
(never offered) · issuing with nothing selected is blocked · duplicate
issue to the same member is blocked.

**Return:** return an issued book · returning an already-returned book is
blocked · availability count is verified correct after return.

**Password:** change password · wrong current password rejected ·
mismatched confirmation rejected · login with the new password succeeds ·
login with the old password fails afterward.

**Reports:** every report type generates · date-filtered search on issue
history · CSV export produces a valid file.

**Dashboard:** all statistics verified against direct database queries ·
refresh pulls fresh numbers (never hard-coded) · logout requires
confirmation and returns to the login screen.

## 12. Common Errors and Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'werkzeug'` | Dependency not installed | `pip install -r requirements.txt` |
| "Invalid username or password" on a login you're sure is correct | Caps Lock / extra space, or you changed the password earlier | Retype carefully; default is `admin` / `admin123` unless changed |
| "Book with this ISBN already exists." | ISBN already in the `books` table | Use a different ISBN, or update the existing record instead |
| "This book cannot be deleted because it is currently issued." | An active row exists in `issued_books` for that book | Return the book first, then delete |
| "Member cannot be deleted because they currently have issued books." | Same as above, for members | Return all of that member's books first |
| "This book is currently unavailable." | `available` = 0 for that book | Wait for a return, or increase quantity via Update Book |
| Dashboard shows `-` for all stats | Database file locked or unreadable | Close other programs using `library.db`, then click Refresh |
| App won't start / blank window | Running a module file directly instead of `main.py` | Always run `python main.py`, not `login.py` etc. |

## 13. Future Enhancements

- Multiple user roles (admin / librarian / student)
- Dedicated student self-service portal
- Email notifications for due dates
- SMS reminders for overdue books
- Barcode / QR code scanning for faster issue & return
- PDF report generation (in addition to CSV)
- Cloud-hosted database (PostgreSQL/MySQL) for multi-branch libraries
- Web-based version (Flask/Django)
- Companion mobile application
- Online fine payment integration
- Book recommendation engine
- Automated backup and restore
- Dark mode UI theme

## 14. Screenshots

_Add screenshots of the Login, Dashboard, Books, Members, Issue/Return and
Reports screens here once you run the app on your machine, e.g.:_

```
![Login Screen](screenshots/login.png)
![Dashboard](screenshots/dashboard.png)
![Books](screenshots/books.png)
![Members](screenshots/members.png)
![Issue / Return](screenshots/issue_return.png)
![Reports](screenshots/reports.png)
```
