"""Add ChatbotConfig table

Revision ID: 003_chatbot
Revises: 002_horario_constraints
Create Date: 2026-03-20
"""
from alembic import op
import sqlalchemy as sa

revision = '003_chatbot'
down_revision = '002_constraints'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('chatbot_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.String(20), nullable=False, server_default='ollama'),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=False, server_default='llama3'),
        sa.Column('ollama_url', sa.String(200), server_default='http://localhost:11434'),
        sa.Column('habilitado', sa.Boolean(), server_default=sa.text('0')),
        sa.Column('max_tokens', sa.Integer(), server_default='1024'),
        sa.Column('temperatura', sa.Float(), server_default='0.3'),
        sa.Column('fecha_actualizacion', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('chatbot_config')
