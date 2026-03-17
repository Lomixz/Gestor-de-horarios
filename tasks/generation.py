"""
Celery task for background schedule generation.

Replaces the threading.Thread approach used in app.py endpoints.
Progress is tracked via Redis (progress.py ProgressTracker).
"""
import logging
import sys
import os

# Ensure /app is in sys.path regardless of how this module is imported
_app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tasks/ -> /app
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from celery_app import celery, create_flask_app

logger = logging.getLogger('tasks.generation')


@celery.task(bind=True, name='tasks.generate_schedules', max_retries=1)
def generate_schedules_task(self, grupos_ids, periodo_academico, version_nombre,
                            creado_por, dias_semana, task_id=None):
    """Generate schedules for given groups in a Celery worker.

    Args:
        grupos_ids: List of group IDs to generate schedules for.
        periodo_academico: Academic period string.
        version_nombre: Version name for the generation.
        creado_por: User ID who initiated the generation.
        dias_semana: List of day names to schedule.
        task_id: Redis progress tracker task_id (from progress.py).
    """
    logger.warning(f"generate_schedules_task START: received task_id={task_id!r}, grupos_ids={grupos_ids!r}")

    app = create_flask_app()

    with app.app_context():
        from progress import get_tracker
        from models import db, HorarioAcademico

        tracker = None
        try:
            tracker = get_tracker()
            tracker._redis.ping()
        except Exception:
            tracker = None

        logger.warning(f"generate_schedules_task: tracker={tracker!r}, task_id after init={task_id!r}")

        # If no task_id was provided, create one now
        if not task_id and tracker:
            task_id = tracker.create(
                total_grupos=len(grupos_ids),
                iniciado_por=creado_por,
            )

        try:
            # Import from helpers to avoid importing the entire 10,000-line app.py
            from app_pkg.helpers.generation_helpers import (
                generar_horarios_masivos_con_progreso,
                _crear_backup_generacion,
            )

            resultado = generar_horarios_masivos_con_progreso(
                grupos_ids=grupos_ids,
                periodo_academico=periodo_academico,
                version_nombre=version_nombre,
                creado_por=creado_por,
                dias_semana=dias_semana,
                task_id=task_id,
            )

            # Create backup/version
            _crear_backup_generacion(grupos_ids, version_nombre, creado_por, resultado)

            # Mark completed
            if tracker and task_id:
                tracker.complete(task_id, resultado['exito'], resultado['mensaje'])

            return {
                'exito': resultado['exito'],
                'mensaje': resultado['mensaje'],
                'horarios_generados': resultado.get('horarios_generados', 0),
                'grupos_procesados': resultado.get('grupos_procesados', 0),
                'task_id': task_id,
            }

        except Exception as e:
            logger.error(f"Error in generate_schedules_task: {e}")
            if tracker and task_id:
                tracker.complete(task_id, False, f"Error: {str(e)}")
            raise
