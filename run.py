"""
run.py
------
Local web server runner.
Starts the Flask Library Management System at http://127.0.0.1:5000
"""

from backend.app import app

if __name__ == "__main__":
    print("==================================================")
    print("Library Management System Web Application")
    print("Local URL: http://127.0.0.1:5000")
    print("Default Admin: admin / admin123")
    print("==================================================")
    app.run(debug=True, host="127.0.0.1", port=5000)
