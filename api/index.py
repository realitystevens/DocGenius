"""
DocGenius Vercel Serverless Function Entry Point
"""

from app.config import create_app
import sys
import os

# Add the parent directory to the path so we can import the app module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Set environment for production
os.environ['FLASK_ENV'] = 'production'


# Create Flask application
app = create_app('production')
