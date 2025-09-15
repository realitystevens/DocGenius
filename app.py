"""
DocGenius Application Entry Point
Modern Flask application with AI-powered document analysis.
"""

import os
from app.config import create_app

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Development server
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=debug_mode
    )
