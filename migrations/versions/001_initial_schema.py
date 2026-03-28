"""Initial schema - stamps existing database structure

Revision ID: 001_initial
Revises:
Create Date: 2026-03-16

This migration creates all tables from scratch for new deployments.
For existing SQLite databases, use migrate_sqlite_to_pg.py first, then stamp this revision:
    flask db stamp 001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Role table
    op.create_table('role',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(50), unique=True, nullable=False),
        sa.Column('descripcion', sa.String(200)),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
    )

    # Carrera table
    op.create_table('carrera',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('codigo', sa.String(20), unique=True, nullable=False),
        sa.Column('descripcion', sa.Text()),
        sa.Column('duracion_cuatrimestres', sa.Integer(), server_default='9'),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
    )

    # User table
    op.create_table('user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(80), unique=True, nullable=False),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('nombre', sa.String(100)),
        sa.Column('apellido', sa.String(100)),
        sa.Column('telefono', sa.String(20)),
        sa.Column('rol', sa.String(20), server_default='profesor_asignatura'),
        sa.Column('tipo_profesor', sa.String(50)),
        sa.Column('imagen_perfil', sa.String(255)),
        sa.Column('firma', sa.String(255)),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('debe_cambiar_password', sa.Boolean(), server_default='false'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ultimo_login', sa.DateTime()),
    )

    # Association tables
    op.create_table('user_roles',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), primary_key=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('role.id'), primary_key=True),
        sa.Column('fecha_asignacion', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('user_carreras',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id'), primary_key=True),
        sa.Column('carrera_id', sa.Integer(), sa.ForeignKey('carrera.id'), primary_key=True),
    )

    # Horario table (time slots)
    op.create_table('horario',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fin', sa.Time(), nullable=False),
        sa.Column('turno', sa.String(20)),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
    )

    # Materia table
    op.create_table('materia',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('codigo', sa.String(20), unique=True, nullable=False),
        sa.Column('horas_semana', sa.Integer(), server_default='4'),
        sa.Column('creditos', sa.Integer()),
        sa.Column('cuatrimestre', sa.Integer()),
        sa.Column('carrera_id', sa.Integer(), sa.ForeignKey('carrera.id')),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('profesor_materias',
        sa.Column('profesor_id', sa.Integer(), sa.ForeignKey('user.id'), primary_key=True),
        sa.Column('materia_id', sa.Integer(), sa.ForeignKey('materia.id'), primary_key=True),
    )

    # Grupo table
    op.create_table('grupo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('codigo', sa.String(20), unique=True, nullable=False),
        sa.Column('nombre', sa.String(100)),
        sa.Column('cuatrimestre', sa.Integer()),
        sa.Column('turno', sa.String(20)),
        sa.Column('carrera_id', sa.Integer(), sa.ForeignKey('carrera.id')),
        sa.Column('max_alumnos', sa.Integer(), server_default='40'),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table('grupo_materias',
        sa.Column('grupo_id', sa.Integer(), sa.ForeignKey('grupo.id'), primary_key=True),
        sa.Column('materia_id', sa.Integer(), sa.ForeignKey('materia.id'), primary_key=True),
    )

    # AsignacionProfesorGrupo
    op.create_table('asignacion_profesor_grupo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profesor_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('materia_id', sa.Integer(), sa.ForeignKey('materia.id'), nullable=False),
        sa.Column('grupo_id', sa.Integer(), sa.ForeignKey('grupo.id'), nullable=False),
        sa.Column('horas_semana', sa.Integer()),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('profesor_id', 'materia_id', 'grupo_id', name='uq_asignacion_profesor_materia_grupo'),
    )

    # DisponibilidadProfesor
    op.create_table('disponibilidad_profesor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profesor_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('horario_id', sa.Integer(), sa.ForeignKey('horario.id'), nullable=False),
        sa.Column('dia_semana', sa.String(10), nullable=False),
        sa.Column('disponible', sa.Boolean(), server_default='true'),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('creado_por', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
    )

    # HorarioAcademico
    op.create_table('horario_academico',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profesor_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('materia_id', sa.Integer(), sa.ForeignKey('materia.id'), nullable=False),
        sa.Column('horario_id', sa.Integer(), sa.ForeignKey('horario.id'), nullable=False),
        sa.Column('dia_semana', sa.String(10), nullable=False),
        sa.Column('grupo', sa.String(10), nullable=False, server_default='A'),
        sa.Column('periodo_academico', sa.String(20)),
        sa.Column('version_nombre', sa.String(100)),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('creado_por', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
    )

    # ConfiguracionSistema
    op.create_table('configuracion_sistema',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('clave', sa.String(100), unique=True, nullable=False),
        sa.Column('valor', sa.Text()),
        sa.Column('tipo', sa.String(20), server_default='string'),
        sa.Column('descripcion', sa.String(500)),
        sa.Column('categoria', sa.String(50)),
        sa.Column('fecha_modificacion', sa.DateTime(), server_default=sa.func.now()),
    )

    # BackupHistory
    op.create_table('backup_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('ruta', sa.String(500)),
        sa.Column('tamano', sa.Integer()),
        sa.Column('tipo', sa.String(50)),
        sa.Column('estado', sa.String(20), server_default='completado'),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('creado_por', sa.Integer(), sa.ForeignKey('user.id')),
    )

    # VersionHorario
    op.create_table('version_horario',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nombre_version', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text()),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('creado_por', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('datos_horarios', sa.Text(), nullable=False),
        sa.Column('total_horarios', sa.Integer(), server_default='0'),
        sa.Column('grupos_afectados', sa.String(500)),
        sa.Column('profesor_origen_id', sa.Integer(), sa.ForeignKey('user.id')),
        sa.Column('carrera_id', sa.Integer(), sa.ForeignKey('carrera.id')),
        sa.Column('activo', sa.Boolean(), server_default='true'),
        sa.Column('restaurado', sa.Boolean(), server_default='false'),
        sa.Column('fecha_restauracion', sa.DateTime()),
    )

    # GeneracionEnProgreso (lock table for concurrent generation)
    op.create_table('generacion_en_progreso',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('grupo_id', sa.Integer(), sa.ForeignKey('grupo.id'), nullable=False, unique=True),
        sa.Column('task_id', sa.String(100), nullable=False),
        sa.Column('iniciado_por', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('fecha_inicio', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('generacion_en_progreso')
    op.drop_table('version_horario')
    op.drop_table('backup_history')
    op.drop_table('configuracion_sistema')
    op.drop_table('horario_academico')
    op.drop_table('disponibilidad_profesor')
    op.drop_table('asignacion_profesor_grupo')
    op.drop_table('grupo_materias')
    op.drop_table('grupo')
    op.drop_table('profesor_materias')
    op.drop_table('materia')
    op.drop_table('horario')
    op.drop_table('user_carreras')
    op.drop_table('user_roles')
    op.drop_table('user')
    op.drop_table('carrera')
    op.drop_table('role')
