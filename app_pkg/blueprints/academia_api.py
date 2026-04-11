"""
API REST académica para integración con sistemas externos (ej. sistema-evaluacion-docente).

Autenticación: header X-API-Key con el valor de la variable de entorno EXTERNAL_API_KEY.

Endpoints disponibles:
    POST /api/ext/auth/login                  — Autenticar cualquier usuario del sistema
    GET  /api/ext/carreras                    — Listar carreras
    GET  /api/ext/carreras/<id>               — Detalle de carrera
    GET  /api/ext/grupos                      — Listar grupos
    GET  /api/ext/grupos/<id>                 — Detalle de grupo
    GET  /api/ext/grupos/<id>/materias        — Materias y profesor por grupo
    GET  /api/ext/asignaciones-grupo          — Registros grupo-carrera-materia-profesor
    GET  /api/ext/cuatrimestres               — Cuatrimestres registrados (distintos)
    GET  /api/ext/relaciones                  — Relaciones docente-materia-carrera
    GET  /api/ext/ping                        — Verificar conectividad (sin auth)
"""
import os
from functools import wraps
from flask import Blueprint, jsonify, request
from models import User, Carrera, Materia, Grupo, AsignacionProfesorGrupo, db

academia_api_bp = Blueprint('academia_api', __name__)

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

def _serialize_carrera(c):
    return {
        'id': c.id,
        'nombre': c.nombre,
        'codigo': c.codigo,
        'descripcion': c.descripcion or None,
        'facultad': c.facultad or None,
        'activa': c.activa,
        'fecha_creacion': c.fecha_creacion.isoformat() if c.fecha_creacion else None,
    }


def _serialize_materia(m):
    return {
        'id': m.id,
        'nombre': m.nombre,
        'codigo': m.codigo,
        'descripcion': m.descripcion or None,
        'cuatrimestre': m.cuatrimestre,
        'creditos': m.creditos,
        'horas_semanales': m.horas_semanales,
        'activa': m.activa,
        'carrera': {
            'id': m.carrera.id,
            'nombre': m.carrera.nombre,
            'codigo': m.carrera.codigo,
        } if m.carrera else None,
    }


def _serialize_carrera_basica(c):
    return {
        'id': c.id,
        'codigo': c.codigo,
        'nombre': c.nombre,
    }


def _serialize_grupo(g):
    return {
        'id': g.id,
        'codigo': g.codigo,
        'numero_grupo': g.numero_grupo,
        'turno': g.turno,
        'cuatrimestre': g.cuatrimestre,
        'activo': g.activo,
        'carrera': _serialize_carrera_basica(g.carrera) if g.carrera else None,
    }


def _serialize_materia_basica(m):
    return {
        'id': m.id,
        'codigo': m.codigo,
        'nombre': m.nombre,
        'cuatrimestre': m.cuatrimestre,
        'activo': m.activa,
    }


def _serialize_profesor_basico(p):
    return {
        'id': p.id,
        'username': p.username,
        'nombre': p.nombre,
        'apellido': p.apellido,
        'nombre_completo': p.get_nombre_completo(),
        'email': p.email,
        'tipo_profesor': p.tipo_profesor or p.rol,
        'activo': p.activo,
    }


def _serialize_user(u):
    """Serializar usuario genérico (para respuesta de login)."""
    return {
        'id': u.id,
        'username': u.username,
        'nombre': u.nombre,
        'apellido': u.apellido,
        'nombre_completo': u.get_nombre_completo(),
        'email': u.email,
        'rol': u.rol,
        'roles': u.get_roles_list(),
        'tipo_profesor': u.tipo_profesor or None,
        'activo': u.activo,
        'carreras': [
            {'id': c.id, 'nombre': c.nombre, 'codigo': c.codigo}
            for c in u.carreras
        ],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@academia_api_bp.route('/api/ext/ping')
def ping():
    """Verificar conectividad con la API (no requiere autenticación)."""
    return jsonify({'status': 'ok', 'message': 'API académica activa'}), 200


# ---- Autenticación --------------------------------------------------------

@academia_api_bp.route('/api/ext/auth/login', methods=['POST'])
@require_api_key
def login():
    """
    Verifica las credenciales de cualquier usuario registrado en el sistema.

    Permite que el sistema externo reutilice las cuentas del Gestor de Horarios
    sin duplicar contraseñas.

    Body JSON:
      { "login": "usuario_o_email", "password": "..." }

    Query param opcional:
      - rol=profesor_completo|profesor_asignatura|admin|jefe_carrera|...
        Si se indica, el usuario DEBE tener ese rol para autenticarse.

    Respuestas:
      200 + datos del usuario  →  credenciales correctas
      401                      →  contraseña incorrecta
      403                      →  cuenta inactiva
      404                      →  usuario no encontrado
    """
    data = request.get_json(silent=True) or {}
    login_val = data.get('login', '').strip()
    password = data.get('password', '')
    rol_requerido = data.get('rol', '').strip() or request.args.get('rol', '').strip()

    if not login_val or not password:
        return jsonify({'error': 'login y password son requeridos'}), 400

    usuario = User.query.filter(
        db.or_(User.username == login_val, User.email == login_val)
    ).first()

    if usuario is None:
        return jsonify({'autenticado': False, 'error': 'Usuario no encontrado'}), 404

    if not usuario.activo:
        return jsonify({'autenticado': False, 'error': 'Cuenta inactiva'}), 403

    if not usuario.check_password(password):
        return jsonify({'autenticado': False, 'error': 'Contraseña incorrecta'}), 401

    # Si se requiere un rol específico, verificarlo
    if rol_requerido and not usuario.has_role(rol_requerido):
        return jsonify({
            'autenticado': False,
            'error': f"El usuario no tiene el rol requerido: {rol_requerido}",
        }), 403

    return jsonify({
        'autenticado': True,
        'usuario': _serialize_user(usuario),
    }), 200


# ---- Carreras -------------------------------------------------------------

@academia_api_bp.route('/api/ext/carreras')
@require_api_key
def listar_carreras():
    """
    Retorna todas las carreras registradas.

    Query params opcionales:
      - activa=true|false   Filtrar por estado activo/inactivo
    """
    query = Carrera.query

    activa_param = request.args.get('activa', '').lower()
    if activa_param == 'true':
        query = query.filter(Carrera.activa == True)
    elif activa_param == 'false':
        query = query.filter(Carrera.activa == False)

    carreras = query.order_by(Carrera.nombre).all()

    return jsonify({
        'total': len(carreras),
        'carreras': [_serialize_carrera(c) for c in carreras],
    }), 200


@academia_api_bp.route('/api/ext/carreras/<int:carrera_id>')
@require_api_key
def detalle_carrera(carrera_id):
    """Retorna los datos de una carrera por su ID, incluyendo sus materias y profesores."""
    carrera = Carrera.query.get(carrera_id)
    if carrera is None:
        return jsonify({'error': 'Carrera no encontrada'}), 404

    data = _serialize_carrera(carrera)

    # Incluir materias activas de la carrera
    materias = Materia.query.filter_by(carrera_id=carrera_id, activa=True).order_by(
        Materia.cuatrimestre, Materia.nombre
    ).all()
    data['materias'] = [_serialize_materia(m) for m in materias]

    # Incluir profesores activos asignados a esta carrera
    profesores = User.query.filter(
        User.carreras.any(id=carrera_id),
        User.rol.in_(ROLES_PROFESOR),
        User.activo == True,
    ).order_by(User.apellido, User.nombre).all()
    data['profesores'] = [_serialize_profesor_basico(p) for p in profesores]

    return jsonify(data), 200


# ---- Grupos ---------------------------------------------------------------

@academia_api_bp.route('/api/ext/grupos')
@require_api_key
def listar_grupos():
    """
    Retorna los grupos registrados en el sistema.

    Query params opcionales:
      - activo=true|false             Filtrar por estado activo/inactivo
      - carrera_id=<int>              Filtrar por carrera
      - cuatrimestre=<int>            Filtrar por cuatrimestre
      - turno=M|V                     Filtrar por turno (M=Matutino, V=Vespertino)
    """
    query = Grupo.query

    activo_param = request.args.get('activo', request.args.get('activa', '')).lower()
    if activo_param == 'true':
        query = query.filter(Grupo.activo == True)
    elif activo_param == 'false':
        query = query.filter(Grupo.activo == False)

    carrera_id_param = request.args.get('carrera_id', '').strip()
    if carrera_id_param.isdigit():
        query = query.filter(Grupo.carrera_id == int(carrera_id_param))

    cuatrimestre_param = request.args.get('cuatrimestre', '').strip()
    if cuatrimestre_param.isdigit():
        query = query.filter(Grupo.cuatrimestre == int(cuatrimestre_param))

    turno_param = request.args.get('turno', '').strip().upper()
    if turno_param:
        if turno_param not in ('M', 'V'):
            return jsonify({'error': 'turno inválido. Valores permitidos: M o V'}), 400
        query = query.filter(Grupo.turno == turno_param)

    grupos = query.join(Carrera, Grupo.carrera_id == Carrera.id).order_by(
        Carrera.nombre, Grupo.cuatrimestre, Grupo.turno, Grupo.numero_grupo
    ).all()

    return jsonify({
        'total': len(grupos),
        'grupos': [_serialize_grupo(g) for g in grupos],
    }), 200


@academia_api_bp.route('/api/ext/grupos/<int:grupo_id>')
@require_api_key
def detalle_grupo(grupo_id):
    """Retorna los datos de un grupo por su ID."""
    grupo = Grupo.query.get(grupo_id)
    if grupo is None:
        return jsonify({'error': 'Grupo no encontrado'}), 404

    return jsonify(_serialize_grupo(grupo)), 200


@academia_api_bp.route('/api/ext/grupos/<int:grupo_id>/materias')
@require_api_key
def materias_por_grupo(grupo_id):
    """
    Retorna el grupo, sus materias y el profesor asignado por materia en ese grupo.
    """
    grupo = Grupo.query.get(grupo_id)
    if grupo is None:
        return jsonify({'error': 'Grupo no encontrado'}), 404

    asignaciones = db.session.query(AsignacionProfesorGrupo, User).join(
        User, AsignacionProfesorGrupo.profesor_id == User.id
    ).filter(
        AsignacionProfesorGrupo.grupo_id == grupo_id,
        AsignacionProfesorGrupo.activo == True,
        User.activo == True,
    ).order_by(User.apellido, User.nombre).all()

    profesor_por_materia = {}
    for asignacion, profesor in asignaciones:
        # Si hay múltiples profesores en la misma materia/grupo, se conserva el primero ordenado.
        if asignacion.materia_id not in profesor_por_materia:
            profesor_por_materia[asignacion.materia_id] = _serialize_profesor_basico(profesor)

    materias_ordenadas = sorted(grupo.materias, key=lambda m: (m.cuatrimestre, m.nombre))
    materias_data = []
    for materia in materias_ordenadas:
        materias_data.append({
            'materia': _serialize_materia_basica(materia),
            'profesor': profesor_por_materia.get(materia.id),
        })

    return jsonify({
        'grupo': _serialize_grupo(grupo),
        'total_materias': len(materias_data),
        'materias': materias_data,
    }), 200


@academia_api_bp.route('/api/ext/asignaciones-grupo')
@require_api_key
def listar_asignaciones_grupo():
    """
    Retorna registros del tipo grupo-carrera-materia-profesor.

    Query params opcionales:
      - activo=true|false             Filtrar por estado activo de la asignación
      - carrera_id=<int>              Filtrar por carrera
      - grupo_id=<int>                Filtrar por grupo
      - cuatrimestre=<int>            Filtrar por cuatrimestre del grupo
      - profesor_id=<int>             Filtrar por profesor
    """
    query = db.session.query(AsignacionProfesorGrupo, Grupo, Materia, User, Carrera).join(
        Grupo, AsignacionProfesorGrupo.grupo_id == Grupo.id
    ).join(
        Materia, AsignacionProfesorGrupo.materia_id == Materia.id
    ).join(
        User, AsignacionProfesorGrupo.profesor_id == User.id
    ).join(
        Carrera, Grupo.carrera_id == Carrera.id
    )

    activo_param = request.args.get('activo', 'true').lower()
    if activo_param == 'true':
        query = query.filter(
            AsignacionProfesorGrupo.activo == True,
            Grupo.activo == True,
            Materia.activa == True,
            User.activo == True,
        )
    elif activo_param == 'false':
        query = query.filter(AsignacionProfesorGrupo.activo == False)

    carrera_id_param = request.args.get('carrera_id', '').strip()
    if carrera_id_param.isdigit():
        query = query.filter(Carrera.id == int(carrera_id_param))

    grupo_id_param = request.args.get('grupo_id', '').strip()
    if grupo_id_param.isdigit():
        query = query.filter(Grupo.id == int(grupo_id_param))

    cuatrimestre_param = request.args.get('cuatrimestre', '').strip()
    if cuatrimestre_param.isdigit():
        query = query.filter(Grupo.cuatrimestre == int(cuatrimestre_param))

    profesor_id_param = request.args.get('profesor_id', '').strip()
    if profesor_id_param.isdigit():
        query = query.filter(User.id == int(profesor_id_param))

    rows = query.order_by(
        Carrera.nombre,
        Grupo.cuatrimestre,
        Grupo.codigo,
        Materia.nombre,
        User.apellido,
        User.nombre,
    ).all()

    asignaciones = [
        {
            'grupo': _serialize_grupo(grupo),
            'carrera': _serialize_carrera_basica(carrera),
            'materia': _serialize_materia_basica(materia),
            'profesor': _serialize_profesor_basico(profesor),
        }
        for _, grupo, materia, profesor, carrera in rows
    ]

    return jsonify({
        'total': len(asignaciones),
        'asignaciones': asignaciones,
    }), 200


# ---- Cuatrimestres --------------------------------------------------------

@academia_api_bp.route('/api/ext/cuatrimestres')
@require_api_key
def listar_cuatrimestres():
    """
    Retorna los cuatrimestres existentes en el sistema (valores distintos de Materia).

    Query params opcionales:
      - carrera_id=<int>   Filtrar por carrera

    Cada cuatrimestre incluye el conteo de materias y la lista de carreras que lo tienen.
    """
    query = db.session.query(
        Materia.cuatrimestre,
        Carrera.id.label('carrera_id'),
        Carrera.nombre.label('carrera_nombre'),
        Carrera.codigo.label('carrera_codigo'),
        db.func.count(Materia.id).label('total_materias'),
    ).join(Carrera, Materia.carrera_id == Carrera.id).filter(Materia.activa == True)

    carrera_id_param = request.args.get('carrera_id', '').strip()
    if carrera_id_param.isdigit():
        query = query.filter(Materia.carrera_id == int(carrera_id_param))

    rows = query.group_by(
        Materia.cuatrimestre, Carrera.id, Carrera.nombre, Carrera.codigo
    ).order_by(Materia.cuatrimestre, Carrera.nombre).all()

    # Agrupar por número de cuatrimestre
    cuatrimestres: dict = {}
    for row in rows:
        num = row.cuatrimestre
        if num not in cuatrimestres:
            cuatrimestres[num] = {
                'numero': num,
                'nombre': f'Cuatrimestre {num}',
                'carreras': [],
                'total_materias': 0,
            }
        cuatrimestres[num]['carreras'].append({
            'id': row.carrera_id,
            'nombre': row.carrera_nombre,
            'codigo': row.carrera_codigo,
            'materias_count': row.total_materias,
        })
        cuatrimestres[num]['total_materias'] += row.total_materias

    result = sorted(cuatrimestres.values(), key=lambda x: x['numero'])

    return jsonify({
        'total': len(result),
        'cuatrimestres': result,
    }), 200


@academia_api_bp.route('/api/ext/cuatrimestres/<int:numero>/materias')
@require_api_key
def materias_por_cuatrimestre(numero):
    """
    Retorna las materias de un cuatrimestre específico.

    Query params opcionales:
      - carrera_id=<int>   Filtrar por carrera
    """
    query = Materia.query.filter_by(cuatrimestre=numero, activa=True)

    carrera_id_param = request.args.get('carrera_id', '').strip()
    if carrera_id_param.isdigit():
        query = query.filter(Materia.carrera_id == int(carrera_id_param))

    materias = query.order_by(Materia.carrera_id, Materia.nombre).all()

    if not materias and not Materia.query.filter_by(cuatrimestre=numero).first():
        return jsonify({'error': f'Cuatrimestre {numero} no encontrado'}), 404

    return jsonify({
        'cuatrimestre': numero,
        'nombre': f'Cuatrimestre {numero}',
        'total': len(materias),
        'materias': [_serialize_materia(m) for m in materias],
    }), 200


# ---- Relaciones docente-materia-carrera -----------------------------------

@academia_api_bp.route('/api/ext/relaciones')
@require_api_key
def listar_relaciones():
    """
    Retorna las relaciones docente-materia-carrera.

    Cada registro representa que un profesor imparte (o puede impartir) una materia
    que pertenece a una carrera determinada.

    Query params opcionales:
      - carrera_id=<int>      Filtrar por carrera
      - cuatrimestre=<int>    Filtrar por cuatrimestre de la materia
      - profesor_id=<int>     Filtrar por profesor
      - activo=true|false     Filtrar por estado del profesor (default: true)
    """
    # Base: profesores con materias asignadas
    query = db.session.query(User, Materia).join(
        Materia, User.materias
    ).join(
        Carrera, Materia.carrera_id == Carrera.id
    ).filter(
        User.rol.in_(ROLES_PROFESOR),
    )

    activo_param = request.args.get('activo', 'true').lower()
    if activo_param == 'true':
        query = query.filter(User.activo == True)
    elif activo_param == 'false':
        query = query.filter(User.activo == False)

    carrera_id_param = request.args.get('carrera_id', '').strip()
    if carrera_id_param.isdigit():
        query = query.filter(Materia.carrera_id == int(carrera_id_param))

    cuatrimestre_param = request.args.get('cuatrimestre', '').strip()
    if cuatrimestre_param.isdigit():
        query = query.filter(Materia.cuatrimestre == int(cuatrimestre_param))

    profesor_id_param = request.args.get('profesor_id', '').strip()
    if profesor_id_param.isdigit():
        query = query.filter(User.id == int(profesor_id_param))

    rows = query.order_by(User.apellido, User.nombre, Materia.cuatrimestre, Materia.nombre).all()

    relaciones = [
        {
            'profesor': _serialize_profesor_basico(profesor),
            'materia': _serialize_materia(materia),
            'carrera': {
                'id': materia.carrera.id,
                'nombre': materia.carrera.nombre,
                'codigo': materia.carrera.codigo,
            } if materia.carrera else None,
        }
        for profesor, materia in rows
    ]

    return jsonify({
        'total': len(relaciones),
        'relaciones': relaciones,
    }), 200
