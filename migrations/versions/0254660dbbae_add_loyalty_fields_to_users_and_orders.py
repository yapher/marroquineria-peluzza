"""add loyalty fields to users and orders

Revision ID: 0254660dbbae
Revises: e0686771e09d
Create Date: 2026-08-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0254660dbbae'
down_revision = 'e0686771e09d'
branch_labels = None
depends_on = None


def upgrade():
    # Obtener inspector para verificar qué columnas existen
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # ==========================================
    # AGREGAR COLUMNAS A USERS (solo si no existen)
    # ==========================================
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'loyalty_points' not in user_columns:
            batch_op.add_column(sa.Column('loyalty_points', sa.Integer(), nullable=True, server_default='0'))
        if 'loyalty_level' not in user_columns:
            batch_op.add_column(sa.Column('loyalty_level', sa.String(length=20), nullable=True, server_default='bronze'))
        if 'total_spent' not in user_columns:
            batch_op.add_column(sa.Column('total_spent', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))
    
    # ==========================================
    # AGREGAR COLUMNA A ORDERS (solo si no existe)
    # ==========================================
    order_columns = [col['name'] for col in inspector.get_columns('orders')]
    
    if 'level_discount' not in order_columns:
        with op.batch_alter_table('orders', schema=None) as batch_op:
            batch_op.add_column(sa.Column('level_discount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'))


def downgrade():
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.drop_column('level_discount')
    
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('total_spent')
        batch_op.drop_column('loyalty_level')
        batch_op.drop_column('loyalty_points')