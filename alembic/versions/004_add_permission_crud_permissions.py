"""add permissions CRUD permissions

Revision ID: 004
Revises: 003
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO permissions (name, description) VALUES
        ('permissions:read', 'Read permissions'),
        ('permissions:write', 'Create/update permissions'),
        ('permissions:delete', 'Delete permissions')
    """)
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r, permissions p
        WHERE r.name = 'admin' AND p.name IN ('permissions:read', 'permissions:write', 'permissions:delete')
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM role_permissions
        WHERE permission_id IN (
            SELECT id FROM permissions
            WHERE name IN ('permissions:read', 'permissions:write', 'permissions:delete')
        )
    """)
    op.execute("""
        DELETE FROM permissions
        WHERE name IN ('permissions:read', 'permissions:write', 'permissions:delete')
    """)
