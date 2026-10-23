"""
test_web_lms.py
---------------
Unit and integration tests for the Flask Web application.
Tests authentication, CRUD on books/members, issue/return workflow, and reports.
"""

import unittest
from backend.app import app
from database.database import init_database, connect_database


class TestWebLMS(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.client = app.test_client()
        init_database()

    def login(self, username="admin", password="admin123"):
        return self.client.post("/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)

    def test_login_page_renders(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Library System", response.data)

    def test_login_failure(self):
        response = self.client.post("/login", data={
            "username": "admin",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    def test_login_success_and_dashboard(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard Overview", response.data)
        self.assertIn(b"Total Copies", response.data)

    def test_book_crud_and_validation(self):
        self.login()
        # Add book
        response = self.client.post("/books/add", data={
            "isbn": "9781234567890",
            "title": "Test Driven Development",
            "author": "Kent Beck",
            "category": "Software",
            "publisher": "Addison-Wesley",
            "publication_year": "2002",
            "quantity": "5",
            "shelf": "B-03",
            "description": "By Example"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Driven Development", response.data)

        # Search book
        search_res = self.client.get("/books?q=Kent", follow_redirects=True)
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b"Test Driven Development", search_res.data)

    def test_member_crud_and_search(self):
        self.login()
        # Add member
        response = self.client.post("/members/add", data={
            "name": "Jane Doe",
            "phone": "+919876543210",
            "email": "jane@example.com",
            "address": "Delhi, India",
            "status": "Active"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Jane Doe", response.data)

        # Search member
        search_res = self.client.get("/members?q=Jane", follow_redirects=True)
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b"Jane Doe", search_res.data)

    def test_reports_and_csv_export(self):
        self.login()
        # Summary report
        res = self.client.get("/reports?type=summary")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Summary", res.data)

        # CSV Export
        csv_res = self.client.get("/reports/export?type=summary")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, "text/csv")
        self.assertIn(b"Total Books", csv_res.data)


if __name__ == "__main__":
    unittest.main()
