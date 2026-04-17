"""
API REST de profesores para integración con sistemas externos.

Autenticación: header X-API-Key con el valor de la variable de entorno EXTERNAL_API_KEY.
"""
import os
from functools import wraps
from flask import Blueprint, jsonify, request
from models import User, Role, db

profesores_api_bp = Blueprint('profesores_api', __name__)

ROLES_PROFESOR = ('profesor_completo', 'profesor_asignatura')


def _filter_es_profesor():
    """
    Condición SQLAlchemy para incluir usuarios con rol de profesor,
    ya sea en el campo legacy 'rol' O en la tabla many-to-many 'roles'.
    """
    return db.or_(
        User.rol.in_(ROLES_PROFESOR),
        User.roles.any(Role.nombre.in_(ROLES_PROFESOR)),
    )


def _get_tipo_profesor(p):
    """
    Devuelve el tipo de profesor revisando todas las fuentes de roles.
    """
    if p.rol in ROLES_PROFESOR:
        return p.rol
    for r in p.roles:
        if r.nombre in ROLES_PROFESOR:
            return r.nombre
    if p.tipo_profesor in ROLES_PROFESOR:
        return p.tipo_profesor
    return None


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
        'tipo_profesor': _get_tipo_profesor(p),
        'roles': p.get_roles_list(),
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
    query = User.query.filter(_filter_es_profesor())

    # Filtro por estado
    activo_param = request.args.get('activo', '').lower()
    if activo_param == 'true':
        query = query.filter(User.activo == True)
    elif activo_param == 'false':
        query = query.filter(User.activo == False)

    # Filtro por tipo de profesor (busca en legacy y en many-to-many)
    tipo_param = request.args.get('tipo', '').strip()
    if tipo_param in ROLES_PROFESOR:
        query = query.filter(db.or_(
            User.rol == tipo_param,
            User.roles.any(Role.nombre == tipo_param),
        ))

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
        _filter_es_profesor(),
    ).first()

    if profesor is None:
        return jsonify({'error': 'Profesor no encontrado'}), 404

    return jsonify(_serialize_profesor(profesor)), 200


@profesores_api_bp.route('/api/auth/profesor', methods=['POST'])
@require_api_key
def autenticar_profesor():
    """
    Verifica las credenciales de un profesor sin exponer su contraseña.
    Acepta username o email indistintamente en el campo 'login'.

    Body JSON:
      { "login": "usuario_o_email", "password": "..." }

    Respuestas:
      200 + datos del profesor  →  credenciales correctas
      401                       →  contraseña incorrecta
      403                       →  usuario inactivo
      404                       →  usuario no encontrado o no es profesor
    """
    data = request.get_json(silent=True) or {}
    login = data.get('login', '').strip()
    password = data.get('password', '')

    if not login or not password:
        return jsonify({'error': 'login y password son requeridos'}), 400

    profesor = User.query.filter(
        db.or_(User.username == login, User.email == login),
        _filter_es_profesor(),
    ).first()

    if profesor is None:
        return jsonify({'autenticado': False, 'error': 'Profesor no encontrado'}), 404

    if not profesor.activo:
        return jsonify({'autenticado': False, 'error': 'Cuenta inactiva'}), 403

    if not profesor.check_password(password):
        return jsonify({'autenticado': False, 'error': 'Contraseña incorrecta'}), 401

    return jsonify({
        'autenticado': True,
        'profesor': _serialize_profesor(profesor),
    }), 200
