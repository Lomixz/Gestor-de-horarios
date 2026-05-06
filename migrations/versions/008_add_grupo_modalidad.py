"""add grupo modalidad and dead hours config

Revision ID: 008
Revises: 007
Create Date: 2026-05-06 03:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_grupo_modalidad'
down_revision = '007_actividad_ptc'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Agregar columna modalidad a tabla grupo
    # Usamos batch_alter_table para compatibilidad si fuera necesario, 
    # pero como es Postgres podemos usar alter_table directamente.
    op.add_column('grupo', sa.Column('modalidad', sa.String(length=20), nullable=False, server_default='regular'))
    
    # 2. Insertar configuraciones iniciales de horas muertas
    # Nota: Usamos execute para insertar datos directos en la migración
    op.execute("""
        INSERT INTO configuracion_sistema (clave, valor, tipo, descripcion, categoria, editable) 
        VALUES 
          ('max_horas_muertas_tc', '2', 'int', 'Horas muertas máximas por día para profesores de tiempo completo', 'horarios', true),
          ('max_horas_muertas_asignatura', '2', 'int', 'Horas muertas máximas por día para profesores por asignatura', 'horarios', true)
        ON CONFLICT (clave) DO NOTHING;
    """)


def downgrade():
    # Eliminar columna modalidad
    op.drop_column('grupo', 'modalidad')
    
    # Eliminar configuraciones
    op.execute("DELETE FROM configuracion_sistema WHERE clave IN ('max_horas_muertas_tc', 'max_horas_muertas_asignatura');")
