"""Add failed_login_attempts and locked_until to User for login lockout

Revision ID: 006_login_lockout
Revises: 005_fix_periodo_academico
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = '006_login_lockout'
down_revision = '005_fix_periodo_academico'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('user', 'locked_until')
    op.drop_column('user', 'failed_login_attempts')
