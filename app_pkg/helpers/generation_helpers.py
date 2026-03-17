"""
Generation helper functions extracted from app.py.

These were moved here to break the circular dependency where
tasks/generation.py had to import the entire 10,000-line app.py.

app.py still re-exports these functions for backwards compatibility.
"""
import threading
import logging

logger = logging.getLogger('sistema_academico')

# ==========================================
# PROGRESO DE GENERACIÓN (Redis-backed)
# ==========================================
# Fallback: dict global para entornos sin Redis (dev local)
# En producción se usa progress.py con Redis
_generacion_progreso_fallback = {
    'activo': False,
    'total_grupos': 0,
    'grupos_procesados': 0,
    'grupo_actual': '',
    'codigo_grupo': '',
    'horarios_generados': 0,
    'mensaje': '',
    'completado': False,
    'exito': False,
    'iniciado': False
}
_progreso_lock = threading.Lock()


def _get_progress_tracker():
    """Get Redis progress tracker, or None if Redis unavailable."""
    try:
        from progress import get_tracker
        tracker = get_tracker()
        tracker._redis.ping()
        return tracker
    except Exception:
        return None


def generar_horarios_masivos_con_progreso(grupos_ids, periodo_academico, version_nombre,
                                           creado_por, dias_semana, task_id=None):
    """Genera horarios actualizando progreso via Redis (o fallback global).

    Args:
        task_id: Redis task_id for progress tracking. If None, uses legacy global dict.
    """
    from generador_horarios_mejorado import GeneradorHorariosMejorado
    from models import Grupo, db

    tracker = _get_progress_tracker() if task_id else None

    def _update_progress(**kwargs):
        if tracker and task_id:
            tracker.update(task_id, **kwargs)
        else:
            with _progreso_lock:
                _generacion_progreso_fallback.update(kwargs)

    def _add_error(grupo_codigo, error_msg, errores_validacion=None):
        if tracker and task_id:
            tracker.add_error(task_id, grupo_codigo, error_msg, errores_validacion)
        else:
            with _progreso_lock:
                if 'errores_detallados' not in _generacion_progreso_fallback:
                    _generacion_progreso_fallback['errores_detallados'] = []
                _generacion_progreso_fallback['errores_detallados'].append({
                    'grupo': grupo_codigo,
                    'error': error_msg,
                    'errores_validacion': errores_validacion or [],
                })

    resultados = {
        'exito': True,
        'mensaje': '',
        'grupos_procesados': 0,
        'grupos_fallidos': 0,
        'horarios_generados': 0,
        'algoritmo': 'Secuencial con Progreso'
    }

    grupos_ordenados = grupos_ids
    total = len(grupos_ordenados)

    for i, grupo_id in enumerate(grupos_ordenados, 1):
        grupo = Grupo.query.get(grupo_id)
        if not grupo:
            continue

        _update_progress(
            grupo_actual=i,
            codigo_grupo=grupo.codigo,
            mensaje=f'Procesando grupo {grupo.codigo}...',
        )

        try:
            db.session.expire_all()

            generador = GeneradorHorariosMejorado(
                grupos_ids=[grupo_id],
                periodo_academico=periodo_academico,
                version_nombre=f"{version_nombre or 'Secuencial'} - {grupo.codigo}",
                creado_por=creado_por,
                dias_semana=dias_semana or ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'],
                tiempo_limite=30
            )

            resultado = generador.generar()

            if resultado['exito']:
                resultados['grupos_procesados'] += 1
                resultados['horarios_generados'] += resultado['horarios_generados']
                _update_progress(
                    grupos_procesados=resultados['grupos_procesados'],
                    horarios_generados=resultados['horarios_generados'],
                )
            else:
                resultados['grupos_fallidos'] += 1
                error_msg = resultado.get('mensaje', 'Error desconocido')
                _add_error(grupo.codigo, error_msg, resultado.get('errores_validacion', []))
                _update_progress(mensaje=f"❌ Error en {grupo.codigo}: {error_msg}")

        except Exception as e:
            db.session.rollback()
            resultados['grupos_fallidos'] += 1
            _add_error(grupo.codigo, str(e))
            _update_progress(mensaje=f"❌ Error en {grupo.codigo}: {str(e)}")
            logger.error(f"Error en grupo {grupo.codigo}: {e}")

    # Resumen final
    if resultados['grupos_procesados'] > 0:
        if resultados['grupos_fallidos'] == 0:
            resultados['mensaje'] = f"✅ Generación exitosa: {resultados['grupos_procesados']} grupos, {resultados['horarios_generados']} horarios"
        else:
            resultados['exito'] = False
            resultados['mensaje'] = f"⚠️ Generación parcial: {resultados['grupos_procesados']} exitosos, {resultados['grupos_fallidos']} fallidos"
    else:
        resultados['exito'] = False
        resultados['mensaje'] = "❌ No se pudo generar ningún horario"

    return resultados


def _crear_backup_generacion(grupos_ids, version_nombre, user_id, resultado):
    """Create version backup after schedule generation (used by both thread and Celery)."""
    if not (resultado.get('exito') or resultado.get('horarios_generados', 0) > 0):
        return
    try:
        import json as _json
        from models import VersionHorario, Grupo as GrupoModel, User, Carrera, HorarioAcademico, db
        from collections import defaultdict

        grupos_por_carrera = defaultdict(list)
        for gid in grupos_ids:
            grupo = GrupoModel.query.get(gid)
            if grupo:
                grupos_por_carrera[grupo.carrera_id].append(grupo.codigo.upper())

        for carrera_id, grupos_codigos in grupos_por_carrera.items():
            horarios_generados = HorarioAcademico.query.filter(
                HorarioAcademico.grupo.in_(grupos_codigos),
                HorarioAcademico.activo == True
            ).all()
            if not horarios_generados:
                continue

            datos = []
            grupos_set = set()
            for h in horarios_generados:
                datos.append({
                    'id': h.id, 'profesor_id': h.profesor_id,
                    'materia_id': h.materia_id, 'horario_id': h.horario_id,
                    'dia_semana': h.dia_semana, 'grupo': h.grupo,
                    'periodo_academico': h.periodo_academico,
                    'version_nombre': h.version_nombre,
                })
                grupos_set.add(h.grupo)

            carrera = Carrera.query.get(carrera_id)
            carrera_nombre = carrera.nombre if carrera else 'Sin carrera'

            version = VersionHorario(
                nombre_version=version_nombre,
                descripcion=f"Generación masiva de {len(grupos_codigos)} grupos ({carrera_nombre})",
                datos_horarios=_json.dumps(datos, ensure_ascii=False),
                total_horarios=len(datos),
                grupos_afectados=','.join(sorted(grupos_set)),
                carrera_id=carrera_id,
                creado_por=user_id,
            )
            db.session.add(version)

        db.session.commit()

        # Limit versions per user
        usuario = User.query.get(user_id)
        limite_versiones = 20 if usuario and usuario.is_admin() else 10
        versiones_usuario = VersionHorario.query.filter(
            VersionHorario.creado_por == user_id,
            VersionHorario.activo == True
        ).order_by(VersionHorario.fecha_creacion.desc()).all()

        if len(versiones_usuario) > limite_versiones:
            for v_old in versiones_usuario[limite_versiones:]:
                v_old.activo = False
            db.session.commit()

    except Exception as e:
        logger.error(f"Error creando backup: {e}")
