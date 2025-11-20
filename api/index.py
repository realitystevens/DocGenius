"""
DocGenius Vercel Serverless Function Entry Point
"""

from app.config import create_app
import sys
import os

# Add the parent directory to the path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# Create Flask application
app = create_app()

# This is required for Vercel
application = app
