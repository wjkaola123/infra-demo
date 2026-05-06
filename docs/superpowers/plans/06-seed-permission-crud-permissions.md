# Plan: Add Permissions CRUD Seed Data Migration

## Context

The permission CRUD API requires `permissions:read`, `permissions:write`, `permissions:delete` permissions to exist. Currently only user/role CRUD permissions exist. This migration seeds the missing permissions and assigns them to the admin role.

## Current State

Seeded permissions (003 migration):
- `users:read`, `users:write`, `users:delete`
- `roles:read`, `roles:write`, `roles:delete`

Missing for permission CRUD:
- `permissions:read` — List/get permissions via API
- `permissions:write` — Create/update permissions via API
- `permissions:delete` — Delete permissions via API

## Migration

### New File

**`alembic/versions/004_add_permission_crud_permissions.py`**

```python
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
    # Insert permissions for the permissions CRUD API
    op.execute("""
        INSERT INTO permissions (name, description) VALUES
        ('permissions:read', 'Read permissions'),
        ('permissions:write', 'Create/update permissions'),
        ('permissions:delete', 'Delete permissions')
    """)

    # Assign all three to admin role
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
```

## Verification

```bash
# Apply migration
docker-compose exec api python -m alembic upgrade head

# Verify permissions exist
docker-compose exec api python -c "
import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text('''
            SELECT p.name, r.name as role_name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN roles r ON r.id = rp.role_id
            WHERE p.name LIKE 'permissions:%'
        '''))
        for row in result.fetchall():
            print(row)

asyncio.run(check())
"
# Expected output:
# ('permissions:read', 'admin')
# ('permissions:write', 'admin')
# ('permissions:delete', 'admin')

# Downgrade
docker-compose exec api python -m alembic downgrade -1
```

## Rollback

- Downgrade deletes the `role_permissions` entries first (foreign key)
- Then deletes the 3 permission rows
- Admin role retains other permissions, editor/viewer unchanged
