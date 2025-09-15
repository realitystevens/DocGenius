"""
Main blueprint for rendering pages and handling non-API routes.
"""

from flask import Blueprint, render_template, current_app, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Render the main application page.

    The index page provides the user interface for:
    - Document upload and management
    - AI-powered document analysis
    - Conversation history
    - File browser
    """
    # Check Redis status for UI display
    redis_status = {
        'available': getattr(current_app, 'redis_available', False),
        'error': getattr(current_app, 'redis_error', None)
    }

    return render_template('index.html', redis_status=redis_status)


@main_bp.route('/health')
def health_check():
    """Health check endpoint with Redis status."""
    redis_available = getattr(current_app, 'redis_available', False)
    redis_error = getattr(current_app, 'redis_error', None)

    status = 'healthy' if redis_available else 'degraded'

    health_data = {
        'status': status,
        'service': 'DocGenius',
        'redis': {
            'available': redis_available,
            'error': redis_error
        }
    }

    return jsonify(health_data), 200 if redis_available else 503


@main_bp.route('/api/redis-status')
def redis_status():
    """Get current Redis connection status."""
    return jsonify({
        'available': getattr(current_app, 'redis_available', False),
        'error': getattr(current_app, 'redis_error', None)
    })
