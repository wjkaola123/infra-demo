# Plan: Create Permission API

## Context

Adding `POST /api/v1/permissions` endpoint to create a new permission. Follows DDD structure with business entity, repository, service, and endpoint layers.

## File Changes

### New Files (4)

**1. `app/entity/permission.py`** — Business entity (domain layer)
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PermissionEntity:
    id: int
    name: str
    description: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

**2. `app/handler/entity/request/permission.py`** — Request DTO
```python
from pydantic import BaseModel, Field, field_validator
import re

class CreatePermissionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+:[a-z0-9_]+$", v):
            raise ValueError("Format must be 'resource:action' with lowercase letters, numbers, underscores")
        return v
```

**3. `app/repository/permission_repository.py`** — Data access
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repository.entity.role import Permission

class PermissionRepository:
    def __init__(self, session: AsyncSession): self.session = session

    async def create(self, name: str, description: str | None) -> Permission:
        perm = Permission(name=name, description=description)
        self.session.add(perm)
        await self.session.commit()
        await self.session.refresh(perm)
        return perm

    async def get_by_name(self, name: str) -> Permission | None:
        result = await self.session.execute(select(Permission).where(Permission.name == name))
        return result.scalar_one_or_none()
```

**4. `app/service/permission_service.py`** — Business logic
```python
from app.repository.permission_repository import PermissionRepository
from app.entity.permission import PermissionEntity
from sqlalchemy.ext.asyncio import AsyncSession

class PermissionService:
    def __init__(self, db: AsyncSession): self.repo = PermissionRepository(db)

    async def create_permission(self, name: str, description: str | None) -> PermissionEntity:
        existing = await self.repo.get_by_name(name)
        if existing:
            raise ValueError("Permission already exists")
        perm = await self.repo.create(name, description)
        return PermissionEntity.model_validate(perm)
```

**5. `app/handler/entity/response/permission.py`** — Response DTO
```python
from pydantic import BaseModel
from datetime import datetime

class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
```

### Modified Files (1)

**6. `app/api/v1/endpoints/permissions.py`** — Add create endpoint
```python
from fastapi import APIRouter, Depends, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, require_permissions
from app.schemas.common import ApiResponse
from app.handler.entity.request.permission import CreatePermissionRequest
from app.handler.entity.response.permission import PermissionResponse
from app.service.permission_service import PermissionService
from app.entity.user import User

router = APIRouter()

@router.post("/", response_model=ApiResponse[PermissionResponse], status_code=status.HTTP_201_CREATED)
async def create_permission(
    body: CreatePermissionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:write"])),
):
    service = PermissionService(db)
    perm = await service.create_permission(body.name, body.description)
    return ApiResponse(data=PermissionResponse.model_validate(perm))
```

**7. `app/api/v1/router.py`** — Wire up permissions router
```python
from app.api.v1.endpoints import permissions as permissions_router
router.include_router(permissions_router.router, prefix="/permissions", tags=["permissions"])
```

### New Test File (1)

**8. `tests/test_api/test_permissions.py`** — Permission API tests
```python
import pytest
import time
from httpx import AsyncClient

async def get_admin_token(client: AsyncClient, db_session, username: str) -> str:
    """Helper to get admin access token with permissions:write."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"{username}_{timestamp}",
        "email": f"{username}_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]
    user_name = register_response.json()["data"]["username"]

    from sqlalchemy import text
    result = await db_session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user_name}
    )
    user_id = result.scalar_one()

    await db_session.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 1)"),
        {"user_id": user_id}
    )
    await db_session.commit()
    return access_token


@pytest.mark.asyncio
async def test_create_permission(client: AsyncClient, db_session):
    """Test creating a new permission."""
    token = await get_admin_token(client, db_session, "createperm")
    timestamp = int(time.time() * 1000)

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"articles:read_{timestamp}", "description": "Read articles"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["name"] == f"articles:read_{timestamp}"
    assert data["data"]["description"] == "Read articles"
    assert "id" in data["data"]
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]


@pytest.mark.asyncio
async def test_create_permission_duplicate_name(client: AsyncClient, db_session):
    """Test creating a permission with duplicate name returns 400."""
    token = await get_admin_token(client, db_session, "dupperm")
    timestamp = int(time.time() * 1000)
    perm_name = f"dup_test_{timestamp}"

    await client.post(
        "/api/v1/permissions/",
        json={"name": perm_name, "description": "First"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": perm_name, "description": "Duplicate"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_permission_invalid_name_format(client: AsyncClient, db_session):
    """Test creating a permission with invalid name format returns 422."""
    token = await get_admin_token(client, db_session, "invperm")

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": "InvalidName", "description": "Bad format"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_permission_requires_auth(client: AsyncClient):
    """Test that creating permission requires authentication."""
    response = await client.post(
        "/api/v1/permissions/",
        json={"name": "test:auth", "description": "Test"}
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_permission_requires_write_permission(client: AsyncClient, db_session):
    """Test that creating permission requires permissions:write."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"nowrite_{timestamp}",
        "email": f"nowrite_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token = register_response.json()["data"]["access_token"]

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"test:noperm_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_permissions(client: AsyncClient, db_session):
    """Test listing all permissions."""
    token = await get_admin_token(client, db_session, "listperm")

    response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    for perm in data["data"]:
        assert "id" in perm
        assert "name" in perm
        assert "description" in perm
```

## Verification

- Run: `docker-compose exec api python -m pytest tests/ -v`
- Run: `docker-compose exec api python -m pytest tests/test_api/test_permissions.py -v`
- Test: `POST /api/v1/permissions` with `{"name": "articles:read", "description": "Read articles"}` → 201
- Duplicate name → 400
- Invalid name format → 422
- No auth → 401/403
- No `permissions:write` permission → 403