"""
desktop/main.py
---------------
Desktop Tkinter Application entry point.
Initializes the database and launches the desktop GUI.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP_DIR = os.path.dirname(os.path.abspath(__file__))
for p in [BASE_DIR, DESKTOP_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from database.database import init_database
import login


def main():
    init_database()
    login.main()


if __name__ == "__main__":
    main()
