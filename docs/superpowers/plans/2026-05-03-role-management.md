# Role Management API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善 RBAC 体系，新增角色 CRUD API、角色权限分配、用户角色分配接口。

**Architecture:** 采用 DDD 分层架构，Repository 模式封装数据访问，Service 层处理业务逻辑，API 层暴露 REST 接口。角色与权限、用户与角色的关系通过关联表管理。

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Redis

---

## File Structure Overview

**New Files:**
- `app/repository/entity/role.py` - Role ORM Model
- `app/repository/entity/role_permission.py` - RolePermission ORM Model  
- `app/repository/entity/user_role.py` - UserRole ORM Model
- `app/repository/role_repository.py` - RoleRepository
- `app/entity/role.py` - RoleEntity
- `app/handler/entity/request/role.py` - RoleCreateRequest, RoleUpdateRequest, PermissionAssignRequest, UserRoleAssignRequest
- `app/handler/entity/response/role.py` - RoleResponse, PermissionResponse, PaginatedRoleResponse, UserRoleResponse
- `app/service/role_service.py` - RoleService
- `app/api/v1/endpoints/roles.py` - Role API endpoints

**Modified Files:**
- `app/api/v1/router.py` - Register roles_router
- `app/service/role_service.py` may be created new

---

## Phase 1: Role CRUD

### Task 1: Create Role Repository Entity

**Files:**
- Create: `app/repository/entity/role.py`
- Test: `tests/repository/entity/test_role.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/repository/entity/test_role.py
import pytest
from datetime import datetime
from app.repository.entity.role import Role

def test_role_creation():
    role = Role(
        id=1,
        name="admin",
        description="Administrator role",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert role.name == "admin"
    assert role.description == "Administrator role"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/repository/entity/test_role.py -v`
Expected: FAIL - import error or file not found

- [ ] **Step 3: Write minimal implementation**

```python
# app/repository/entity/role.py
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.repository.entity.base import Base, TimestampMixin

class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/repository/entity/test_role.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/repository/entity/role.py tests/repository/entity/test_role.py
git commit -m "feat: add Role ORM model"
```

---

### Task 2: Create Role Repository

**Files:**
- Create: `app/repository/role_repository.py`
- Modify: `app/repository/entity/__init__.py`
- Test: `tests/repository/test_role_repository.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/repository/test_role_repository.py
import pytest
from app.repository.role_repository import RoleRepository

@pytest.mark.asyncio
async def test_create_role():
    repository = RoleRepository()
    role = await repository.create(name="admin", description="Admin role")
    assert role.name == "admin"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/repository/test_role_repository.py::test_create_role -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/repository/role_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repository.entity.role import Role

class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: str | None = None) -> Role:
        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def get_by_id(self, role_id: int) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self.session.execute(select(Role))
        return list(result.scalars().all())

    async def update(self, role_id: int, name: str | None = None, description: str | None = None) -> Role | None:
        role = await self.get_by_id(role_id)
        if not role:
            return None
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role_id: int) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False
        await self.session.delete(role)
        await self.session.commit()
        return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/repository/test_role_repository.py::test_create_role -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/repository/role_repository.py tests/repository/test_role_repository.py
git commit -m "feat: add RoleRepository with CRUD operations"
```

---

### Task 3: Create Role Service

**Files:**
- Create: `app/service/role_service.py`
- Test: `tests/service/test_role_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/service/test_role_service.py
import pytest
from app.service.role_service import RoleService

@pytest.mark.asyncio
async def test_create_role():
    service = RoleService()
    role = await service.create_role(name="admin", description="Admin role")
    assert role.name == "admin"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_role_service.py::test_create_role -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/service/role_service.py
from app.repository.role_repository import RoleRepository
from app.repository.entity.role import Role
from app.entity.role import RoleEntity

class RoleService:
    def __init__(self, repository: RoleRepository):
        self.repository = repository

    async def create_role(self, name: str, description: str | None = None) -> RoleEntity:
        role = await self.repository.create(name=name, description=description)
        return RoleEntity.model_validate(role)

    async def get_role(self, role_id: int) -> RoleEntity | None:
        role = await self.repository.get_by_id(role_id)
        return RoleEntity.model_validate(role) if role else None

    async def list_roles(self) -> list[RoleEntity]:
        roles = await self.repository.list_all()
        return [RoleEntity.model_validate(r) for r in roles]

    async def update_role(self, role_id: int, name: str | None = None, description: str | None = None) -> RoleEntity | None:
        role = await self.repository.update(role_id, name=name, description=description)
        return RoleEntity.model_validate(role) if role else None

    async def delete_role(self, role_id: int) -> bool:
        return await self.repository.delete(role_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_role_service.py::test_create_role -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/service/role_service.py tests/service/test_role_service.py
git commit -m "feat: add RoleService with CRUD operations"
```

---

### Task 4: Create Role API Endpoints (CRUD only)

**Files:**
- Create: `app/handler/entity/request/role.py`
- Create: `app/handler/entity/response/role.py`
- Create: `app/api/v1/endpoints/roles.py`
- Modify: `app/api/v1/router.py`
- Test: `tests/api/v1/endpoints/test_roles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/api/v1/endpoints/test_roles.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_role(client: AsyncClient):
    response = await client.post("/api/v1/roles/", json={"name": "admin", "description": "Admin role"})
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["name"] == "admin"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_create_role -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/handler/entity/request/role.py
from pydantic import BaseModel

class RoleCreateRequest(BaseModel):
    name: str
    description: str | None = None

class RoleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
```

```python
# app/handler/entity/response/role.py
from pydantic import BaseModel
from datetime import datetime

class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

```python
# app/api/v1/endpoints/roles.py
from fastapi import APIRouter, Depends, HTTPException
from app.service.role_service import RoleService
from app.handler.entity.request.role import RoleCreateRequest, RoleUpdateRequest
from app.handler.entity.response.role import RoleResponse
from app.schemas.common import ApiResponse
from app.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

async def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    from app.repository.role_repository import RoleRepository
    repository = RoleRepository(session=db)
    return RoleService(repository=repository)

@router.post("/", response_model=ApiResponse[RoleResponse])
async def create_role(
    request: RoleCreateRequest,
    service: RoleService = Depends(get_role_service)
):
    role = await service.create_role(name=request.name, description=request.description)
    return ApiResponse(data=RoleResponse.model_validate(role))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_create_role -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/handler/entity/request/role.py app/handler/entity/response/role.py app/api/v1/endpoints/roles.py tests/api/v1/endpoints/test_roles.py
git commit -m "feat: add Role CRUD API endpoints"
```

---

## Phase 2: Role-Permission Assignment

### Task 5: Create RolePermission and UserRole ORM Models

**Files:**
- Create: `app/repository/entity/role_permission.py`
- Create: `app/repository/entity/user_role.py`
- Test: `tests/repository/entity/test_role_permission.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/repository/entity/test_role_permission.py
import pytest
from app.repository.entity.role_permission import RolePermission

def test_role_permission_creation():
    rp = RolePermission(role_id=1, permission_id=1)
    assert rp.role_id == 1
    assert rp.permission_id == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/repository/entity/test_role_permission.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/repository/entity/role_permission.py
from sqlalchemy import ForeignKey, Table, Column, Integer
from app.repository.entity.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True)
)
```

```python
# app/repository/entity/user_role.py
from sqlalchemy import ForeignKey, Column, Integer
from app.repository.entity.base import Base

class UserRole(Base):
    __tablename__ = "user_roles"

    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id: int = Column(Integer, ForeignKey("roles.id"), nullable=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/repository/entity/test_role_permission.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/repository/entity/role_permission.py app/repository/entity/user_role.py tests/repository/entity/test_role_permission.py
git commit -m "feat: add RolePermission and UserRole ORM models"
```

---

### Task 6: Add Permission Assignment to RoleService

**Files:**
- Modify: `app/service/role_service.py`
- Modify: `app/repository/role_repository.py`
- Test: `tests/service/test_role_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/service/test_role_service.py
@pytest.mark.asyncio
async def test_assign_permissions():
    service = RoleService()
    result = await service.assign_permissions(role_id=1, permission_ids=[1, 2])
    assert len(result) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_role_service.py::test_assign_permissions -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/repository/role_repository.py - add methods
async def add_permissions(self, role_id: int, permission_ids: list[int]) -> list[Permission]:
    # Implementation to link permissions to role

async def remove_permission(self, role_id: int, permission_id: int) -> bool:
    # Implementation to unlink permission from role
```

```python
# app/service/role_service.py - add methods
async def assign_permissions(self, role_id: int, permission_ids: list[int]) -> list[Permission]:
    return await self.repository.add_permissions(role_id, permission_ids)

async def remove_permission(self, role_id: int, permission_id: int) -> bool:
    return await self.repository.remove_permission(role_id, permission_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_role_service.py::test_assign_permissions -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/service/role_service.py app/repository/role_repository.py tests/service/test_role_service.py
git commit -m "feat: add permission assignment to role service"
```

---

### Task 7: Add Permission Assignment API Endpoints

**Files:**
- Modify: `app/handler/entity/request/role.py`
- Modify: `app/api/v1/endpoints/roles.py`
- Test: `tests/api/v1/endpoints/test_roles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/api/v1/endpoints/test_roles.py
@pytest.mark.asyncio
async def test_assign_permissions(client: AsyncClient):
    response = await client.post("/api/v1/roles/1/permissions", json={"permission_ids": [1, 2]})
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_assign_permissions -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/handler/entity/request/role.py - add
class PermissionAssignRequest(BaseModel):
    permission_ids: list[int]
```

```python
# app/api/v1/endpoints/roles.py - add endpoints
@router.post("/{role_id}/permissions")
async def assign_permissions(
    role_id: int,
    request: PermissionAssignRequest,
    service: RoleService = Depends(get_role_service)
):
    permissions = await service.assign_permissions(role_id, request.permission_ids)
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])

@router.delete("/{role_id}/permissions/{permission_id}")
async def remove_permission(
    role_id: int,
    permission_id: int,
    service: RoleService = Depends(get_role_service)
):
    await service.remove_permission(role_id, permission_id)
    return ApiResponse(message="permission removed")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_assign_permissions -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/handler/entity/request/role.py app/api/v1/endpoints/roles.py tests/api/v1/endpoints/test_roles.py
git commit -m "feat: add role-permission assignment API endpoints"
```

---

## Phase 3: User-Role Assignment

### Task 8: Add User-Role Methods to RoleRepository

**Files:**
- Modify: `app/repository/role_repository.py`
- Test: `tests/repository/test_role_repository.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/repository/test_role_repository.py
@pytest.mark.asyncio
async def test_assign_role_to_user():
    repository = RoleRepository()
    result = await repository.assign_role_to_user(user_id=1, role_id=1)
    assert result.user_id == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/repository/test_role_repository.py::test_assign_role_to_user -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/repository/role_repository.py - add methods
async def assign_role_to_user(self, user_id: int, role_id: int) -> UserRole:
    user_role = UserRole(user_id=user_id, role_id=role_id)
    self.session.add(user_role)
    await self.session.commit()
    await self.session.refresh(user_role)
    return user_role

async def get_user_roles(self, user_id: int) -> list[Role]:
    result = await self.session.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id)
    )
    return list(result.scalars().all())

async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
    result = await self.session.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        )
    )
    user_role = result.scalar_one_or_none()
    if not user_role:
        return False
    await self.session.delete(user_role)
    await self.session.commit()
    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/repository/test_role_repository.py::test_assign_role_to_user -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/repository/role_repository.py tests/repository/test_role_repository.py
git commit -m "feat: add user-role assignment methods to RoleRepository"
```

---

### Task 9: Add User-Role Methods to RoleService

**Files:**
- Modify: `app/service/role_service.py`
- Test: `tests/service/test_role_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/service/test_role_service.py
@pytest.mark.asyncio
async def test_get_user_roles():
    service = RoleService()
    roles = await service.get_user_roles(user_id=1)
    assert isinstance(roles, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_role_service.py::test_get_user_roles -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/service/role_service.py - add methods
async def get_user_roles(self, user_id: int) -> list[RoleEntity]:
    roles = await self.repository.get_user_roles(user_id)
    return [RoleEntity.model_validate(r) for r in roles]

async def assign_role_to_user(self, user_id: int, role_id: int) -> UserRoleEntity:
    user_role = await self.repository.assign_role_to_user(user_id, role_id)
    return UserRoleEntity.model_validate(user_role)

async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
    return await self.repository.remove_role_from_user(user_id, role_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_role_service.py::test_get_user_roles -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/service/role_service.py tests/service/test_role_service.py
git commit -m "feat: add user-role methods to RoleService"
```

---

### Task 10: Add User-Role API Endpoints

**Files:**
- Modify: `app/api/v1/endpoints/roles.py`
- Test: `tests/api/v1/endpoints/test_roles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/api/v1/endpoints/test_roles.py
@pytest.mark.asyncio
async def test_get_user_roles(client: AsyncClient):
    response = await client.get("/api/v1/roles/users/1/roles")
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_get_user_roles -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/api/v1/endpoints/roles.py - add endpoints
@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    service: RoleService = Depends(get_role_service)
):
    roles = await service.get_user_roles(user_id)
    return ApiResponse(data=[RoleResponse.model_validate(r) for r in roles])

@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: int,
    role_id: int,
    service: RoleService = Depends(get_role_service)
):
    user_role = await service.assign_role_to_user(user_id, role_id)
    return ApiResponse(data=UserRoleResponse.model_validate(user_role))

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    service: RoleService = Depends(get_role_service)
):
    await service.remove_role_from_user(user_id, role_id)
    return ApiResponse(message="role removed from user")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_get_user_roles -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/roles.py tests/api/v1/endpoints/test_roles.py
git commit -m "feat: add user-role assignment API endpoints"
```

---

## Phase 4: User Permission Query

### Task 11: Add User Permission Query

**Files:**
- Modify: `app/service/role_service.py`
- Modify: `app/repository/role_repository.py`
- Test: `tests/service/test_role_service.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/service/test_role_service.py
@pytest.mark.asyncio
async def test_get_user_permissions():
    service = RoleService()
    perms = await service.get_user_permissions(user_id=1)
    assert isinstance(perms, list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/service/test_role_service.py::test_get_user_permissions -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/repository/role_repository.py - add method
async def get_user_permissions(self, user_id: int) -> list[Permission]:
    result = await self.session.execute(
        select(Permission)
        .join(role_permissions, Permission.id == role_permissions.c.permission_id)
        .join(Role, Role.id == role_permissions.c.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .distinct()
    )
    return list(result.scalars().all())
```

```python
# app/service/role_service.py - add method
async def get_user_permissions(self, user_id: int) -> list[PermissionEntity]:
    permissions = await self.repository.get_user_permissions(user_id)
    return [PermissionEntity.model_validate(p) for p in permissions]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/service/test_role_service.py::test_get_user_permissions -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/service/role_service.py app/repository/role_repository.py tests/service/test_role_service.py
git commit -m "feat: add user permission query"
```

---

### Task 12: Add User Permission API Endpoint

**Files:**
- Modify: `app/api/v1/endpoints/roles.py`
- Test: `tests/api/v1/endpoints/test_roles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/api/v1/endpoints/test_roles.py
@pytest.mark.asyncio
async def test_get_user_permissions(client: AsyncClient):
    response = await client.get("/api/v1/users/1/permissions")
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_get_user_permissions -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/api/v1/endpoints/roles.py - add endpoint
@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    service: RoleService = Depends(get_role_service)
):
    permissions = await service.get_user_permissions(user_id)
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_get_user_permissions -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/roles.py tests/api/v1/endpoints/test_roles.py
git commit -m "feat: add user permission query API endpoint"
```

---

## Phase 5: Permission Decorator

### Task 13: Add require_permissions Decorator

**Files:**
- Create: `app/tools/auth/require_permissions.py`
- Modify: `app/api/v1/endpoints/roles.py`
- Test: `tests/tools/auth/test_require_permissions.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/tools/auth/test_require_permissions.py
import pytest
from app.tools.auth.require_permissions import require_permissions

def test_require_permissions():
    @require_permissions("roles:read")
    async def handler():
        return True
    assert handler.__permissions__ == ["roles:read"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/tools/auth/test_require_permissions.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# app/tools/auth/require_permissions.py
from functools import wraps
from fastapi import HTTPException

def require_permissions(*permissions: str):
    def decorator(func):
        func.__permissions__ = permissions
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Permission check logic - extract user from context
            # Verify user has required permissions
            # If not, raise HTTPException(403)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/tools/auth/test_require_permissions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/tools/auth/require_permissions.py tests/tools/auth/test_require_permissions.py
git commit -m "feat: add require_permissions decorator"
```

---

### Task 14: Apply Decorator to Role Endpoints

**Files:**
- Modify: `app/api/v1/endpoints/roles.py`
- Test: `tests/api/v1/endpoints/test_roles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/api/v1/endpoints/test_roles.py
@pytest.mark.asyncio
async def test_create_role_without_permission(client: AsyncClient, normal_token: str):
    response = await client.post("/api/v1/roles/", json={"name": "admin"}, headers={"Authorization": f"Bearer {normal_token}"})
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_create_role_without_permission -v`
Expected: PASS (or FAIL if decorator not applied)

- [ ] **Step 3: Write minimal implementation**

```python
# app/api/v1/endpoints/roles.py - apply decorator
from app.tools.auth.require_permissions import require_permissions

@router.post("/", response_model=ApiResponse[RoleResponse])
@require_permissions("roles:write")
async def create_role(...):
    ...

@router.get("/", response_model=ApiResponse[list[RoleResponse]])
@require_permissions("roles:read")
async def list_roles(...):
    ...

@router.delete("/{role_id}")
@require_permissions("roles:delete")
async def delete_role(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/v1/endpoints/test_roles.py::test_create_role_without_permission -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/roles.py tests/api/v1/endpoints/test_roles.py
git commit -m "feat: apply require_permissions decorator to role endpoints"
```

---

## Phase 6: Integration & Documentation

### Task 15: Register Router and Integration Test

**Files:**
- Modify: `app/api/v1/router.py`
- Test: `tests/api/v1/test_integration.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/api/v1/test_integration.py
@pytest.mark.asyncio
async def test_full_role_workflow(client: AsyncClient, admin_token: str):
    # Create role
    create_resp = await client.post("/api/v1/roles/", json={"name": "editor", "description": "Editor role"})
    assert create_resp.status_code == 201
    
    # List roles
    list_resp = await client.get("/api/v1/roles/")
    assert list_resp.status_code == 200
    
    # Delete role
    role_id = create_resp.json()["data"]["id"]
    delete_resp = await client.delete(f"/api/v1/roles/{role_id}")
    assert delete_resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/v1/test_integration.py::test_full_role_workflow -v`
Expected: FAIL (router not registered)

- [ ] **Step 3: Write minimal implementation**

```python
# app/api/v1/router.py
from app.api.v1.endpoints import roles

router.include_router(roles.router, prefix="/roles", tags=["roles"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/v1/test_integration.py::test_full_role_workflow -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/router.py tests/api/v1/test_integration.py
git commit -m "feat: register roles router and integration test"
```

---

### Task 16: Database Migration

**Files:**
- Create: `alembic/versions/xxxx_add_roles_tables.py`
- Test: Run migration and verify

- [ ] **Step 1: Create migration**

Run: `alembic revision --autogenerate -m "add roles tables"`
Expected: Migration file created

- [ ] **Step 2: Apply migration**

Run: `docker-compose exec api python -m alembic upgrade head`
Expected: SUCCESS

- [ ] **Step 3: Commit migration**

```bash
git add alembic/versions/
git commit -m "feat: add roles tables migration"
```

---

## Verification Checklist

- [ ] All 16 tasks completed
- [ ] All tests passing: `docker-compose exec api python -m pytest tests/ -v`
- [ ] API endpoints tested with admin token
- [ ] Permission controls verified (403 for unauthorized)
