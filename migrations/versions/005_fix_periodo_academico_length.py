"""Fix periodo_academico column length from VARCHAR(20) to VARCHAR(50)

Revision ID: 005_fix_periodo_academico
Revises: 004_session_id
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = '005_fix_periodo_academico'
down_revision = '004_session_id'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'horario_academico',
        'periodo_academico',
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=True,
    )
    op.alter_column(
        'asignacion_profesor_grupo',
        'periodo_academico',
        existing_type=sa.String(length=50),
        type_=sa.String(length=50),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        'horario_academico',
        'periodo_academico',
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
