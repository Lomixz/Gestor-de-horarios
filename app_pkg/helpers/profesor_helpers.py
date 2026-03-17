"""
Professor-related helper functions.

Contains functions for managing professor workload and file validation.
Extracted from app.py lines 95-139 and 6523-6532.
"""

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/gif'}


def obtener_limite_horas_profesor(tipo_profesor):
    """
    Obtiene el límite de horas semanales para un tipo de profesor.
    Los valores se configuran desde el panel de administración.
    """
    from models import ConfiguracionSistema

    tipo_lower = (tipo_profesor or '').lower().strip()

    if 'tiempo completo' in tipo_lower or 'tiempo_completo' in tipo_lower:
        return ConfiguracionSistema.get_config('horas_tiempo_completo', 40)
    elif 'asignatura' in tipo_lower:
        return ConfiguracionSistema.get_config('horas_asignatura', 20)
    elif 'medio tiempo' in tipo_lower or 'medio_tiempo' in tipo_lower:
        return ConfiguracionSistema.get_config('horas_medio_tiempo', 20)
    else:
        # Tipo no reconocido: usar límite de asignatura como default
        return ConfiguracionSistema.get_config('horas_asignatura', 20)


def obtener_horas_actuales_profesor(profesor_id):
    """
    Calcula las horas actuales asignadas a un profesor.
    """
    from models import HorarioAcademico
    return HorarioAcademico.query.filter_by(profesor_id=profesor_id, activo=True).count()


def validar_carga_horaria_profesor(profesor):
    """
    Valida si un profesor puede recibir más horas de clase.
    Retorna tuple: (puede_asignar, horas_actuales, limite, horas_disponibles)
    """
    from models import ConfiguracionSistema

    horas_actuales = obtener_horas_actuales_profesor(profesor.id)
    limite = obtener_limite_horas_profesor(profesor.tipo_profesor)
    limite_absoluto = ConfiguracionSistema.get_config('horas_limite_absoluto', 50)

    # El límite efectivo es el menor entre el límite del tipo y el absoluto
    limite_efectivo = min(limite, limite_absoluto)
    horas_disponibles = max(0, limite_efectivo - horas_actuales)
    puede_asignar = horas_disponibles > 0

    return (puede_asignar, horas_actuales, limite_efectivo, horas_disponibles)


def allowed_file(filename, file_obj=None):
    """Verificar si el archivo tiene una extensión y MIME type permitidos"""
    ext_ok = '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    if file_obj and hasattr(file_obj, 'content_type'):
        return ext_ok and file_obj.content_type in ALLOWED_MIME_TYPES
    return ext_ok
