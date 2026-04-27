"""Add session_id to User

Revision ID: 004_session_id
Revises: 003_chatbot
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_session_id'
down_revision = '003_chatbot'
branch_labels = None
depends_on = None

def upgrade():
    # Add session_id column to user table
    op.add_column('user', sa.Column('session_id', sa.String(length=100), nullable=True))

def downgrade():
    op.drop_column('user', 'session_id')
