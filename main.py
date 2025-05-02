#!/usr/bin/env python3
"""
Main entry point for the Data Center Chatbot application.
Imports the Flask app from app.py.
"""

from app import app

# This allows running the app with 'gunicorn main:app'
# The actual implementation is in app.py

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
