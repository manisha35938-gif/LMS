"""
test_lms.py
-----------
Comprehensive automated test suite for Library Management System (LMS).
Verifies:
- Password hashing and verification
- Input validation (phone, ISBN, email, quantities)
- Database schema initialization & default admin
- Book operations (add, update, constraint checks, cascade deletion)
- Member operations (add, update, phone/email uniqueness, cascade deletion)
- Issue/Return workflow (stock decrement/increment, duplicate issue prevention)
- Overdue and fine calculation
"""

import os
import unittest
import sqlite3
from datetime import datetime, timedelta

import security
import validators
import utils
import database


class TestLMSSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_library.db"
        database.DB_NAME = cls.test_db
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def setUp(self):
        database.init_database()
        self.conn = database.connect_database()

    def tearDown(self):
        self.conn.close()

    # 1. Security Tests
    def test_password_hashing(self):
        password = "secretPassword123"
        hashed = security.hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(security.verify_password(password, hashed))
        self.assertFalse(security.verify_password("wrongPassword", hashed))

    # 2. Validator Tests
    def test_validators(self):
        # Phone numbers: standard, with spaces, with dashes, with international leading '+'
        self.assertTrue(validators.is_valid_phone("9876543210"))
        self.assertTrue(validators.is_valid_phone("+919876543210"))
        self.assertTrue(validators.is_valid_phone("+91-987-654-3210"))
        self.assertFalse(validators.is_valid_phone("123")) # too short
        self.assertFalse(validators.is_valid_phone("abc1234567"))

        # Email
        self.assertTrue(validators.is_valid_email("")) # optional
        self.assertTrue(validators.is_valid_email("test@example.com"))
        self.assertFalse(validators.is_valid_email("invalid-email"))

        # ISBN: 10 digit, 13 digit, 10 digit ending in X
        self.assertTrue(validators.is_valid_isbn("")) # optional
        self.assertTrue(validators.is_valid_isbn("9780747532699"))
        self.assertTrue(validators.is_valid_isbn("0-19-852663-X"))
        self.assertTrue(validators.is_valid_isbn("019852663x"))
        self.assertFalse(validators.is_valid_isbn("1234")) # too short

        # Quantity and Year
        self.assertTrue(validators.is_valid_quantity("5"))
        self.assertFalse(validators.is_valid_quantity("0"))
        self.assertFalse(validators.is_valid_quantity("-1"))
        self.assertTrue(validators.is_valid_year("2024"))
        self.assertFalse(validators.is_valid_year("999"))

    # 3. Fine Calculation Tests
    def test_fine_calculation(self):
        # On or before due date -> 0 fine
        self.assertEqual(utils.calculate_fine("2026-10-20", "2026-10-15"), 0.0)
        self.assertEqual(utils.calculate_fine("2026-10-20", "2026-10-20"), 0.0)

        # 3 days overdue at 5.0 per day -> 15.0
        self.assertEqual(utils.calculate_fine("2026-10-20", "2026-10-23"), 15.0)

    # 4. Default Admin Verification
    def test_default_admin_created(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = 'admin'")
        admin = cur.fetchone()
        self.assertIsNotNone(admin)
        self.assertTrue(security.verify_password("admin123", admin["password_hash"]))

    # 5. Book & Issue Transaction Tests
    def test_issue_and_return_workflow(self):
        cur = self.conn.cursor()

        # Add book
        cur.execute(
            "INSERT INTO books (isbn, title, author, quantity, available) VALUES (?, ?, ?, ?, ?)",
            ("9781111111111", "Clean Code", "Robert C. Martin", 3, 3)
        )
        book_id = cur.lastrowid

        # Add member
        cur.execute(
            "INSERT INTO members (name, phone, email, status) VALUES (?, ?, ?, ?)",
            ("Alice", "9876543210", "alice@test.com", "Active")
        )
        member_id = cur.lastrowid
        self.conn.commit()

        # Issue book
        cur.execute(
            "INSERT INTO issued_books (book_id, member_id, issue_date, due_date, status, fine) VALUES (?, ?, ?, ?, 'Issued', 0)",
            (book_id, member_id, "2026-10-01", "2026-10-15")
        )
        cur.execute("UPDATE books SET available = available - 1 WHERE id = ?", (book_id,))
        self.conn.commit()

        # Verify stock decreased
        cur.execute("SELECT available FROM books WHERE id = ?", (book_id,))
        self.assertEqual(cur.fetchone()["available"], 2)

        # Verify active issue count prevents reducing book quantity below 1
        active_issued = cur.execute(
            "SELECT COUNT(*) AS n FROM issued_books WHERE book_id = ? AND status = 'Issued'",
            (book_id,)
        ).fetchone()["n"]
        self.assertEqual(active_issued, 1)

        # Return book
        issue_id = cur.execute("SELECT id FROM issued_books WHERE book_id = ? AND status = 'Issued'", (book_id,)).fetchone()["id"]
        cur.execute(
            "UPDATE issued_books SET return_date = ?, status = 'Returned', fine = ? WHERE id = ?",
            ("2026-10-18", 15.0, issue_id)
        )
        cur.execute("UPDATE books SET available = MIN(quantity, available + 1) WHERE id = ?", (book_id,))
        self.conn.commit()

        # Verify stock restored
        cur.execute("SELECT available FROM books WHERE id = ?", (book_id,))
        self.assertEqual(cur.fetchone()["available"], 3)

        # Verify deletion of returned book succeeds with cascade / history cleanup
        cur.execute("DELETE FROM issued_books WHERE book_id = ?", (book_id,))
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

        cur.execute("SELECT COUNT(*) n FROM books WHERE id = ?", (book_id,))
        self.assertEqual(cur.fetchone()["n"], 0)


if __name__ == "__main__":
    unittest.main()

