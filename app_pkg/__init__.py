"""
Application factory for Gestor de Horarios.

Usage:
    from app_pkg import create_app
    app = create_app('production')

NOTE: During the transition period, the legacy app.py is still the primary
entry point. This factory can be used for new deployments and testing.
"""
import os
import logging
import secrets

from flask import Flask, jsonify

from .config import config


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    app.config.from_object(config[config_name])

    # Secret key management
    if not app.config['SECRET_KEY']:
        app.config['SECRET_KEY'] = _get_secret_key()

    # Connection pooling for PostgreSQL
    if 'postgresql' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
        app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {
            'pool_size': 10,
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'max_overflow': 20,
        })

    # Initialize extensions
    _init_extensions(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Setup logging
    _setup_logging(app)

    return app


def _get_secret_key():
    """Get or generate secret key from file."""
    key_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'instance', '.secret_key'
    )
    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    with open(key_file, 'w') as f:
        f.write(key)
    return key


def _init_extensions(app):
    """Initialize Flask extensions with the app."""
    from .extensions import db, migrate, login_manager, csrf, limiter, cache

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure rate limiter storage
    redis_url = app.config.get('REDIS_URL', 'memory://')
    limiter_storage = f"{redis_url}/1" if redis_url != 'memory://' else 'memory://'
    limiter.init_app(app, storage_uri=limiter_storage)

    # Configure cache
    if 'redis' in redis_url:
        cache.init_app(app, config={
            'CACHE_TYPE': 'RedisCache',
            'CACHE_REDIS_URL': redis_url,
            'CACHE_DEFAULT_TIMEOUT': 300,
        })
    else:
        cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))


def _register_blueprints(app):
    """Register all application blueprints."""
    from .blueprints.auth import auth_bp
    from .blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')


def _register_error_handlers(app):
    """Register error handlers."""
    from .exceptions import AppError

    @app.errorhandler(AppError)
    def handle_app_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso no encontrado'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Error interno del servidor'}), 500


def _setup_logging(app):
    """Configure application logging."""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log', encoding='utf-8'),
            logging.StreamHandler(),
        ]
    )
