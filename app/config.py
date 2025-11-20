"""
Application factory and configuration for DocGenius Flask app.
"""

import os
from flask import Flask
from dotenv import load_dotenv
from app.database.db_service import DatabaseService

load_dotenv()


def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Configure the app
    app.config.from_object(get_config_class(config_name))

    # Initialize SQLite database
    # Use /tmp for Vercel, instance folder for local
    if os.environ.get('VERCEL'):
        instance_path = '/tmp'
    else:
        instance_path = app.instance_path
        os.makedirs(instance_path, exist_ok=True)

    db_path = os.path.join(instance_path, 'docgenius.db')

    db_service = DatabaseService(db_path)
    app.db_service = db_service
    app.db_available = True

    print(f"✓ SQLite database initialized at {db_path}")

    # Configure session to use filesystem
    app.config['SESSION_TYPE'] = 'filesystem'
    session_dir = os.path.join(instance_path, 'sessions')
    app.config['SESSION_FILE_DIR'] = session_dir
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SECURE'] = app.config.get(
        'SECURE_COOKIES', False)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Ensure session directory exists
    os.makedirs(session_dir, exist_ok=True)

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
        """Ensure every user has a unique session ID and exists in database."""
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())

        # Ensure user exists in database
        try:
            app.db_service.create_user(session['user_id'])
        except Exception as e:
            app.logger.error(f"Error creating user in database: {str(e)}")

        # Add request timestamp for debugging
        if app.debug:
            session['last_request'] = str(uuid.uuid1())
