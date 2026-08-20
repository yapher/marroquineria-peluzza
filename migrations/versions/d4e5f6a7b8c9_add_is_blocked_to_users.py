# migrations/versions/d4e5f6a7b8c9_add_is_blocked_to_users.py
"""add is_blocked to users

Revision ID: d4e5f6a7b8c9
Revises: 9fa80b1b728e
Create Date: 2026-08-20
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = '9fa80b1b728e'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = [col['name'] for col in inspector.get_columns('users')]

    if 'is_blocked' not in user_columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    'is_blocked',
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.text('0')
                )
            )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_blocked')