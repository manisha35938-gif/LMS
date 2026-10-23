"""
api/index.py
------------
Serverless WSGI entry point for Vercel deployment.
Vercel automatically detects the 'app' WSGI instance here and routes incoming requests.
"""

from backend.app import app

# Vercel entry point
if __name__ == "__main__":
    app.run()
