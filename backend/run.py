#!/usr/bin/env python3
"""Opportunity Finder Backend Server

Run this script to start the Flask development server.

Usage:
    python run.py
    or
    flask run --port=5000
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from config import settings

# Create Flask app
app = create_app()

if __name__ == "__main__":
    # Run development server
    print("Starting Opportunity Finder Backend...")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Frontend URL: {settings.FRONTEND_URL}")
    print("Server running at: http://localhost:5001")
    print()
    print("API Endpoints:")
    print("  - Health: http://localhost:5001/health")
    print("  - Auth:   http://localhost:5001/api/v1/auth/...")
    print("  - User:   http://localhost:5001/api/v1/user/...")
    print("  - Opportunities: http://localhost:5001/api/v1/opportunities/...")
    print()
    app.run(host="0.0.0.0", port=5001, debug=settings.DEBUG)
