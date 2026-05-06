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

**3. `app/service/permission_service.py`** — Add list method
```python
async def list_permissions(self, page: int, page_size: int, name: str | None) -> dict:
    items, total = await self.repo.list_paginated(page, page_size, name)
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": [PermissionEntity.model_validate(p) for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
```

**4. `app/api/v1/endpoints/permissions.py`** — Add list endpoint
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
    result = await service.list_permissions(page, page_size, name)
    return ApiResponse(data=PaginatedPermissionResponse(
        items=[PermissionResponse.model_validate(p) for p in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    ))
```

## Verification

- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Test: `GET /api/v1/permissions?page=1&page_size=10&name=articles`
- Empty filter: `GET /api/v1/permissions`