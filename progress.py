"""
Redis-based progress tracker for schedule generation.

Replaces the global `generacion_progreso` dict + threading.Lock
that doesn't work across multiple Gunicorn workers.

Each generation task gets a unique task_id (UUID).
Progress is stored in Redis hashes with TTL of 1 hour.
"""
import json
import os
import uuid

import redis


def get_redis_client():
    """Get Redis client from environment or default."""
    url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    return redis.from_url(url, decode_responses=True)


class ProgressTracker:
    """Track generation progress in Redis, accessible across all workers."""

    PREFIX = 'generation:'
    TTL = 3600  # 1 hour

    def __init__(self, redis_client=None):
        self._redis = redis_client or get_redis_client()

    def _key(self, task_id):
        return f'{self.PREFIX}{task_id}'

    def create(self, total_grupos, iniciado_por=None):
        """Start tracking a new generation task. Returns the task_id."""
        task_id = str(uuid.uuid4())
        data = {
            'task_id': task_id,
            'activo': 'true',
            'total_grupos': str(total_grupos),
            'grupos_procesados': '0',
            'grupo_actual': '0',
            'codigo_grupo': 'Iniciando...',
            'horarios_generados': '0',
            'mensaje': 'Iniciando generación...',
            'completado': 'false',
            'exito': 'false',
            'iniciado_por': str(iniciado_por or ''),
            'errores_detallados': '[]',
        }
        key = self._key(task_id)
        self._redis.hset(key, mapping=data)
        self._redis.expire(key, self.TTL)
        return task_id

    def update(self, task_id, **fields):
        """Update one or more fields of a generation task."""
        key = self._key(task_id)
        mapped = {}
        for k, v in fields.items():
            if isinstance(v, bool):
                mapped[k] = 'true' if v else 'false'
            elif isinstance(v, (list, dict)):
                mapped[k] = json.dumps(v, ensure_ascii=False)
            else:
                mapped[k] = str(v)
        if mapped:
            self._redis.hset(key, mapping=mapped)
            self._redis.expire(key, self.TTL)

    def add_error(self, task_id, grupo_codigo, error_msg, errores_validacion=None):
        """Append an error to the detailed error list."""
        key = self._key(task_id)
        raw = self._redis.hget(key, 'errores_detallados') or '[]'
        errores = json.loads(raw)
        errores.append({
            'grupo': grupo_codigo,
            'error': error_msg,
            'errores_validacion': errores_validacion or [],
        })
        self._redis.hset(key, 'errores_detallados', json.dumps(errores, ensure_ascii=False))

    def get(self, task_id):
        """Get full progress data for a task. Returns dict or None."""
        key = self._key(task_id)
        data = self._redis.hgetall(key)
        if not data:
            return None

        # Convert string booleans and numbers back
        result = {}
        for k, v in data.items():
            if v in ('true', 'false'):
                result[k] = v == 'true'
            elif k in ('total_grupos', 'grupos_procesados', 'grupo_actual', 'horarios_generados'):
                try:
                    result[k] = int(v)
                except ValueError:
                    result[k] = v
            elif k == 'errores_detallados':
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = []
            else:
                result[k] = v
        return result

    def complete(self, task_id, exito, mensaje):
        """Mark a generation task as completed."""
        self.update(task_id,
                    completado=True,
                    exito=exito,
                    mensaje=mensaje,
                    activo=False)

    def delete(self, task_id):
        """Remove a generation task from Redis."""
        self._redis.delete(self._key(task_id))


# Module-level singleton
_tracker = None


def get_tracker():
    """Get or create the module-level ProgressTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
