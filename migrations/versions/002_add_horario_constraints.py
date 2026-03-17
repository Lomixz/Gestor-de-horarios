"""Add unique constraints to prevent double-booking

Revision ID: 002_constraints
Revises: 001_initial
Create Date: 2026-03-16

Adds partial unique indexes on horario_academico to prevent:
- Same professor teaching two classes at the same time/day
- Same group having two classes at the same time/day
Only applies to active records (activo = true).
"""
from alembic import op
import sqlalchemy as sa

revision = '002_constraints'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Prevent double-booking a professor: same professor, same time slot, same day
    op.create_index(
        'ix_horario_profesor_active',
        'horario_academico',
        ['profesor_id', 'horario_id', 'dia_semana'],
        unique=True,
        postgresql_where=sa.text('activo = true'),
    )

    # Prevent double-booking a group: same group, same time slot, same day
    op.create_index(
        'ix_horario_grupo_active',
        'horario_academico',
        ['grupo', 'horario_id', 'dia_semana'],
        unique=True,
        postgresql_where=sa.text('activo = true'),
    )


def downgrade():
    op.drop_index('ix_horario_grupo_active', table_name='horario_academico')
    op.drop_index('ix_horario_profesor_active', table_name='horario_academico')
