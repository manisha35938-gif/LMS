"""
database/database.py
--------------------
SQLite connection management, table creation, and default admin provisioning.
Supports local execution as well as serverless platforms like Vercel (using /tmp).
"""

import os
import shutil
import sqlite3
from datetime import datetime

# Resolve base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FOLDER = os.path.join(BASE_DIR, "database")

# In Vercel serverless functions, the root filesystem is read-only except /tmp
if os.environ.get("VERCEL"):
    DB_DIR = "/tmp"
    DB_NAME = os.path.join(DB_DIR, "library.db")
    if not os.path.exists(DB_NAME):
        src_db = os.path.join(DB_FOLDER, "library.db")
        if os.path.exists(src_db):
            try:
                shutil.copyfile(src_db, DB_NAME)
            except Exception:
                pass
else:
    DB_DIR = DB_FOLDER
    DB_NAME = os.path.join(DB_DIR, "library.db")

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def connect_database():
    """Return a new sqlite3 connection with foreign keys enabled and Row objects."""
    db_dir = os.path.dirname(DB_NAME)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all tables if they do not exist."""
    conn = connect_database()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT UNIQUE,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT,
                publisher TEXT,
                publication_year INTEGER,
                quantity INTEGER NOT NULL,
                available INTEGER NOT NULL,
                shelf TEXT,
                description TEXT,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                email TEXT UNIQUE,
                address TEXT,
                registration_date TEXT,
                status TEXT DEFAULT 'Active'
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS issued_books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                status TEXT NOT NULL DEFAULT 'Issued',
                fine REAL DEFAULT 0,
                FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
    finally:
        conn.close()


def ensure_default_admin():
    """Ensure the default administrator account exists."""
    from backend.security import hash_password

    conn = connect_database()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM users")
        count = cur.fetchone()["count"]

        if count == 0:
            cur.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (
                    DEFAULT_ADMIN_USERNAME,
                    hash_password(DEFAULT_ADMIN_PASSWORD),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
    finally:
        conn.close()


def init_database():
    """Entry point called at application startup."""
    create_tables()
    ensure_default_admin()
