"""
Application factory and configuration for DocGenius Flask app.
"""

import os
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv

# Try to import Redis - it's optional for development
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠ Redis not installed - using filesystem sessions for development")

load_dotenv()


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Configure the app
    app.config.from_object(get_config_class(config_name))

    # Initialize Redis client - MANDATORY for application
    redis_client = None
    redis_available = False
    redis_error = None

    # Redis configuration is required
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_url = os.getenv("REDIS_URL")

    if not REDIS_AVAILABLE:
        redis_error = "Redis package not installed. Please install with: pip install redis"
        app.logger.error(redis_error)
    else:
        try:
            if redis_url:
                # Use Redis URL (for production/Heroku)
                redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                # Use individual Redis settings
                redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    decode_responses=True
                )

            # Test Redis connection - MANDATORY
            redis_client.ping()
            redis_available = True
            print(
                f"✓ Redis connection established at {redis_host}:{redis_port}")

        except Exception as e:
            redis_error = f"Redis connection failed: {str(e)}"
            app.logger.error(redis_error)
            redis_client = None
            redis_available = False

    # Configure Flask-Session with Redis ONLY
    if redis_available and redis_client:
        app.config['SESSION_TYPE'] = 'redis'
        app.config['SESSION_REDIS'] = redis_client
        app.config['SESSION_PERMANENT'] = False
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_COOKIE_SECURE'] = app.config.get(
            'SECURE_COOKIES', False)
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

        Session(app)
    else:
        # Store error for UI display - NO fallback sessions
        app.config['REDIS_ERROR'] = redis_error or "Redis connection required but not available"

    # Store redis client and status in app
    app.redis_client = redis_client
    app.redis_available = redis_available
    app.redis_error = redis_error
    app.redis_available = redis_available

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register before request handlers
    register_before_request_handlers(app)

    return app


def get_config_class(config_name):
    """Get configuration class based on environment."""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    return configs.get(config_name, DevelopmentConfig)


class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv(
        'SECRET_KEY', 'dev-secret-key-please-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.pdf', '.txt', '.docx', '.pptx']

    # AI Configuration
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro-latest')

    # Rate limiting
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SECURE_COOKIES = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECURE_COOKIES = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SECURE_COOKIES = False


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.blueprints.main import main_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def register_error_handlers(app):
    """Register error handlers."""
    from flask import jsonify, render_template, request

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found', 'status_code': 404}), 404
        return render_template('errors/404.html'), 404
        # return render_template('index.html'), 200

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'status_code': 500}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 16MB.', 'status_code': 413}), 413


def register_before_request_handlers(app):
    """Register before request handlers."""
    import uuid
    from flask import session, request

    @app.before_request
    def ensure_user_session():
        """Ensure every user has a unique session ID."""
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())

        # Add request timestamp for debugging
        if app.debug:
            session['last_request'] = str(uuid.uuid1())