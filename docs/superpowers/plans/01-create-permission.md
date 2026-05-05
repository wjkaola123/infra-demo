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

## Verification

- Run: `docker-compose exec api python -m pytest tests/ -v`
- Test: `POST /api/v1/permissions` with `{"name": "articles:read", "description": "Read articles"}` → should return 201 with permission data
- Duplicate name test: should return 400 error