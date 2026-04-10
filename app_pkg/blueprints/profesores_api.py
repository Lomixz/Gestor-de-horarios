"""
API REST de profesores para integración con sistemas externos.

Autenticación: header X-API-Key con el valor de la variable de entorno EXTERNAL_API_KEY.
"""
import os
from functools import wraps
from flask import Blueprint, jsonify, request
from models import User, db

profesores_api_bp = Blueprint('profesores_api', __name__)

ROLES_PROFESOR = ('profesor_completo', 'profesor_asignatura')


# ---------------------------------------------------------------------------
# Autenticación por API Key
# ---------------------------------------------------------------------------

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key', '').strip()
        expected = os.environ.get('EXTERNAL_API_KEY', '')
        if not expected or key != expected:
            return jsonify({'error': 'API Key inválida o ausente'}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Serialización
# ---------------------------------------------------------------------------

def _serialize_profesor(p):
    return {
        'id': p.id,
        'username': p.username,
        'nombre': p.nombre,
        'apellido': p.apellido,
        'nombre_completo': p.get_nombre_completo(),
        'email': p.email,
        'telefono': p.telefono or None,
        'tipo_profesor': p.tipo_profesor or p.rol,
        'rol': p.rol,
        'activo': p.activo,
        'fecha_registro': p.fecha_registro.isoformat() if p.fecha_registro else None,
        'carreras': [
            {'id': c.id, 'nombre': c.nombre, 'codigo': c.codigo}
            for c in p.carreras
        ],
        'materias': [
            {'id': m.id, 'nombre': m.nombre, 'codigo': m.codigo}
            for m in p.materias
        ],
        'disponibilidad': [
            {
                'dia': d.dia_semana,
                'hora_inicio': d.horario.get_hora_inicio_str() if d.horario else None,
                'hora_fin': d.horario.get_hora_fin_str() if d.horario else None,
                'disponible': d.disponible,
            }
            for d in p.disponibilidades
            if d.activo
        ],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@profesores_api_bp.route('/api/profesores/ping')
def ping():
    """Verificar conectividad con la API (no requiere autenticación)."""
    return jsonify({'status': 'ok', 'message': 'API de profesores activa'}), 200


@profesores_api_bp.route('/api/profesores')
@require_api_key
def listar_profesores():
    """
    Retorna la lista de profesores.

    Query params opcionales:
      - activo=true|false   Filtrar por estado activo/inactivo
      - tipo=profesor_completo|profesor_asignatura
      - carrera_id=<int>    Filtrar por carrera
    """
    query = User.query.filter(User.rol.in_(ROLES_PROFESOR))

    # Filtro por estado
    activo_param = request.args.get('activo', '').lower()
    if activo_param == 'true':
        query = query.filter(User.activo == True)
    elif activo_param == 'false':
        query = query.filter(User.activo == False)

    # Filtro por tipo de profesor
    tipo_param = request.args.get('tipo', '').strip()
    if tipo_param in ROLES_PROFESOR:
        query = query.filter(User.tipo_profesor == tipo_param)

    # Filtro por carrera
    carrera_id_param = request.args.get('carrera_id', '').strip()
    if carrera_id_param.isdigit():
        query = query.filter(User.carreras.any(id=int(carrera_id_param)))

    profesores = query.order_by(User.apellido, User.nombre).all()

    return jsonify({
        'total': len(profesores),
        'profesores': [_serialize_profesor(p) for p in profesores],
    }), 200


@profesores_api_bp.route('/api/profesores/<int:profesor_id>')
@require_api_key
def detalle_profesor(profesor_id):
    """Retorna los datos completos de un profesor por su ID."""
    profesor = User.query.filter(
        User.id == profesor_id,
        User.rol.in_(ROLES_PROFESOR),
    ).first()

    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado'}), 404

    return jsonify(_serialize_profesor(profesor)), 200
