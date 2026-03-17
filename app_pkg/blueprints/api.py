"""
API blueprint for JSON endpoints.

NOTE: During transition, most API routes still live in app.py.
This blueprint provides the health check endpoint and will
gradually absorb other API routes.
"""
from flask import Blueprint, jsonify
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger('sistema_academico')


@api_bp.route('/health')
def health_check():
    """Health check endpoint verifying DB, Redis, and Celery worker."""
    status = {'status': 'healthy', 'services': {}}

    # Check database
    try:
        from models import db
        db.session.execute(db.text('SELECT 1'))
        status['services']['database'] = 'ok'
    except Exception as e:
        status['services']['database'] = f'error: {str(e)}'
        status['status'] = 'degraded'

    # Check Redis
    try:
        from progress import get_redis_client
        client = get_redis_client()
        client.ping()
        status['services']['redis'] = 'ok'
    except Exception as e:
        status['services']['redis'] = f'error: {str(e)}'
        status['status'] = 'degraded'

    # Check Celery worker
    try:
        from celery_app import celery
        inspector = celery.control.inspect(timeout=2.0)
        active = inspector.active()
        if active is None:
            status['services']['celery'] = 'no workers'
            status['status'] = 'degraded'
        else:
            status['services']['celery'] = 'ok'
    except Exception as e:
        status['services']['celery'] = f'error: {str(e)}'
        status['status'] = 'degraded'

    http_status = 200 if status['status'] == 'healthy' else 503
    return jsonify(status), http_status
