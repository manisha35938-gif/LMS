# 📚 Library Management System (LMS)

A complete, production-ready **Library Management System** built with **Python, Flask, Tailwind CSS, SQLite, and Tkinter** — deployable to **Vercel** as a responsive web app and runnable as an offline desktop application.

Developed as a B.Tech Computer Science project, it centralizes book inventory, member records, borrowing/returning workflows, overdue fine calculations, and analytics reports.

---

## 🚀 Live Cloud Deployment on Vercel

This repository is pre-configured for **1-click serverless deployment on [Vercel](https://vercel.com/)** via [`vercel.json`](vercel.json) and [`api/index.py`](api/index.py).

### How to Deploy on Vercel in 3 Steps:

1. **Push your code to GitHub**:
   * Double-click `push_to_github.bat` or run:
     ```bash
     git push -u origin main
     ```
2. **Import into Vercel**:
   * Go to [vercel.com/new](https://vercel.com/new) and log in with your GitHub account.
   * Select your repository: **`manisha35938-gif/LMS`**.
3. **Click Deploy**:
   * Keep the default settings (Vercel automatically detects `vercel.json` and Python 3 runtime).
   * Click **Deploy**. Your LMS will be live on a `*.vercel.app` URL in under 60 seconds!

---

## 📁 Clean Project Architecture

```
LMS / (Library Management System)
│
├── api/
│   └── index.py               # Vercel Serverless Function entry point
│
├── backend/
│   ├── __init__.py
│   ├── app.py                 # Core Flask web application & REST routes
│   ├── security.py            # Password hashing & verification (Werkzeug)
│   ├── validators.py          # Input validation (phone, ISBN, email, quantities)
│   └── utils.py               # Loan rules (14-day limit, ₹5/day fine, dates)
│
├── database/
│   ├── __init__.py
│   ├── database.py            # SQLite connection manager & auto-provisioning
│   ├── schema.sql             # SQL schema with ON DELETE CASCADE constraints
│   └── library.db             # Initial SQLite database with starter records
│
├── frontend/
│   ├── static/
│   │   ├── css/style.css      # Custom styles and scrollbars
│   │   └── js/main.js         # Interactive search, modals & notification alerts
│   └── templates/
│       ├── base.html          # Responsive Tailwind CSS layout (sidebar + navbar)
│       ├── login.html         # User authentication card
│       ├── dashboard.html     # Live KPI stats, recent transactions, low stock alerts
│       ├── books.html         # Book catalog with search & edit/add modals
│       ├── members.html       # Member directory with search & edit/add modals
│       ├── issue_return.html  # Book loan workflow, active loans & return fine calculation
│       ├── reports.html       # Analytics dashboard & one-click CSV export
│       └── change_password.html # Password update interface
│
├── desktop/                   # Offline Tkinter desktop GUI
│   ├── main.py                # Desktop entry point
│   ├── login.py               # Desktop login window
│   ├── dashboard.py           # Desktop dashboard window
│   ├── books.py               # Desktop books window
│   ├── members.py             # Desktop members window
│   ├── issue_return.py        # Desktop issue & return window
│   ├── reports.py             # Desktop reports & CSV window
│   ├── change_password.py     # Desktop password change window
│   ├── style.py               # Shared desktop ttk styles & color palette
│   └── utils.py               # Desktop Tkinter dialog wrappers
│
├── .github/workflows/ci-cd.yml # GitHub Actions automated testing & build pipeline
├── vercel.json                # Vercel serverless routing configuration
├── requirements.txt           # Python dependencies (Flask, Werkzeug)
├── run.py                     # Local web application runner (http://127.0.0.1:5000)
├── main.py                    # Root entry point
├── test_lms.py                # Backend unit & integration test suite
├── test_web_lms.py            # Web application test suite
├── start_web.bat              # One-click Windows Web Launcher
├── start_desktop.bat          # One-click Windows Desktop GUI Launcher
├── start_library_system.bat   # Universal Launcher (Web or Desktop)
├── build_exe.bat              # Compiles standalone Windows .exe with PyInstaller
├── push_to_github.bat         # One-click script to push code to GitHub
├── .gitignore                 # Git ignore rules
└── README.md
```

---

## 💻 How to Run Locally

### 1. Web Application (Recommended for Browser):
Double-click [`start_web.bat`](start_web.bat) or run in terminal:
```bash
pip install -r requirements.txt
python run.py
```
Open **`http://127.0.0.1:5000`** in your browser.

### 2. Desktop GUI Application (Tkinter):
Double-click [`start_desktop.bat`](start_desktop.bat) or run:
```bash
python desktop/main.py
```

---

## 🔑 Default Credentials

| Role | Username | Password |
|---|---|---|
| **Administrator** | `admin` | `admin123` |

> *You can change this password after logging in via the **Change Password** page.*

---

## ⚙️ Features & Business Rules

1. **Authentication**: Salted password hashing via `Werkzeug` (never stored in plain text).
2. **Dashboard**: Live database counts (Total Copies, Available Copies, Currently Issued, Members, Overdue) + Recent Transactions + Low Stock Alert (&le; 2 copies).
3. **Books**: Add, edit, delete, search. Validates positive quantities, 8-13 digit ISBNs (including ISBN-10 check digits). Prevents reducing quantity below the count of active loans.
4. **Members**: Add, edit, delete, search. Duplicate phone and email prevention.
5. **Issue & Return**:
   * Issue duration: **14 days**.
   * Checks real-time stock availability.
   * Blocks duplicate loans of the same book to the same member.
   * Auto-calculates overdue fines at **₹5.00 / day overdue**.
6. **Reports & CSV Export**:
   * Summary overview
   * Overdue books list with days overdue
   * Most issued books ranking
   * Active borrowers
   * Date-filtered loan history
   * **Export to CSV**: Generates Excel-friendly UTF-8 CSV files with BOM.
7. **Foreign Key Integrity**: Enforced with `ON DELETE CASCADE`.

---

## 🧪 Automated Testing

Run the test suites locally to verify backend and web application health:
```bash
python test_lms.py
python test_web_lms.py
```
*Both suites pass with 100% OK status.*
