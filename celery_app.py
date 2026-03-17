"""
Celery application for background task processing.

Usage:
    celery -A celery_app worker --loglevel=info --concurrency=2
"""
import os
import sys

# Ensure the app directory is in sys.path so forked worker processes
# can import modules like 'models', 'progress', etc.
_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from celery import Celery

celery = Celery(
    'gestor_horarios',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['tasks.generation'],
)

celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    worker_max_tasks_per_child=50,
    task_soft_time_limit=300,   # 5 min soft limit
    task_time_limit=600,        # 10 min hard limit
)


def create_flask_app():
    """Create Flask app for Celery worker context."""
    import sys
    import os
    # Re-insert /app on every call in case the forked worker reset sys.path
    _dir = os.path.dirname(os.path.abspath(__file__))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

    from flask import Flask
    from models import db

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///instance/sistema_academico.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 5,
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'max_overflow': 10,
        }

    db.init_app(app)
    return app
