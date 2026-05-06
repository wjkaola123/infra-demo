# Plan: List Permissions API

## Context

Adding `GET /api/v1/permissions` endpoint with pagination and name filter. Reuses infrastructure created in create-permission plan.

## Prerequisite

**Run migration `004` first** — `permissions:read` must exist and be assigned to admin role before implementing this endpoint.

```bash
docker-compose exec api python -m alembic upgrade head
```

## File Changes

### New/Modified Files

**1. `app/handler/entity/response/permission.py`** — Add paginated response
```python
class PaginatedPermissionResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**2. `app/repository/permission_repository.py`** — Add list_paginated method
```python
async def list_paginated(self, page: int, page_size: int, name: str | None = None) -> tuple[list[Permission], int]:
    offset = (page - 1) * page_size
    base_query = select(Permission)
    count_query = select(func.count(Permission.id))

    if name:
        name_filter = Permission.name.ilike(f"%{name}%")
        base_query = base_query.where(name_filter)
        count_query = count_query.where(name_filter)

    count_result = await self.session.execute(count_query)
    total = count_result.scalar() or 0

    result = await self.session.execute(
        base_query.offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total
```

**3. `app/service/permission_service.py`** — Add list method (DDD: ORM → Domain Entity)
```python
async def list_permissions(self, page: int, page_size: int, name: str | None) -> tuple[list[PermissionEntity], int, dict]:
    items, total = await self.repo.list_paginated(page, page_size, name)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    entities = [
        PermissionEntity(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in items
    ]
    return entities, total, {"page": page, "page_size": page_size, "total_pages": total_pages}
```

**4. `app/api/v1/endpoints/permissions.py`** — Add list endpoint (DDD: Domain Entity → Response DTO)
```python
@router.get("/", response_model=ApiResponse[PaginatedPermissionResponse])
async def list_permissions(
    page: int = 1,
    page_size: int = 20,
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:read"])),
):
    service = PermissionService(db)
    entities, total, meta = await service.list_permissions(page, page_size, name)
    return ApiResponse(data=PaginatedPermissionResponse(
        items=[PermissionResponse.model_validate(e) for e in entities],
        total=total,
        page=meta["page"],
        page_size=meta["page_size"],
        total_pages=meta["total_pages"],
    ))
```

## Data Flow (DDD)

```
DB (permissions table)
  ↓ ORM: Permission (SQLAlchemy model)
Repository
  ↓ Conversion: Permission → PermissionEntity
Service
  ↓ Conversion: PermissionEntity → PermissionResponse
Handler/Endpoint
  ↓
API Response (JSON)
```

Service 层手动将 ORM 的 `Permission` 转成 `PermissionEntity`，endpoint 再用 Pydantic 的 `model_validate` 把 `PermissionEntity` 转成 `PermissionResponse`。

## Verification

- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Test: `GET /api/v1/permissions?page=1&page_size=10&name=articles`
- Empty filter: `GET /api/v1/permissions`