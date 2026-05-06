"""Add actividad_ptc table for PTC professor non-teaching hours

Revision ID: 007_actividad_ptc
Revises: 006_login_lockout
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = '007_actividad_ptc'
down_revision = '006_login_lockout'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'actividad_ptc',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('profesor_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('horario_id', sa.Integer(), sa.ForeignKey('horario.id'), nullable=False),
        sa.Column('dia_semana', sa.String(length=10), nullable=False),
        sa.Column('tipo_actividad', sa.String(length=20), nullable=False),
        sa.Column('notas', sa.String(length=200), nullable=True),
        sa.Column('periodo_academico', sa.String(length=50), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_actividad_ptc_slot',
        'actividad_ptc',
        ['profesor_id', 'horario_id', 'dia_semana'],
        unique=True,
        postgresql_where=sa.text('activo = true'),
    )


def downgrade():
    op.drop_index('ix_actividad_ptc_slot', table_name='actividad_ptc')
    op.drop_table('actividad_ptc')
