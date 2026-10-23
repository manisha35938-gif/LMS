"""
main.py
--------
Application entry point. Initializes the database (creating it and the
default admin account if needed) and then launches the login screen.
Run this file to start the application - do not run any other module
directly.
"""

from database import init_database
import login


def main():
    init_database()
    login.main()


if __name__ == "__main__":
    main()
