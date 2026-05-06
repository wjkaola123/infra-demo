# Plan: Get Permission API

## Context

Adding `GET /api/v1/permissions/{id}` endpoint to fetch a single permission by ID.

## Prerequisite

**Run migration `004` first** — `permissions:read` must exist and be assigned to admin role before implementing this endpoint.

```bash
docker-compose exec api python -m alembic upgrade head
```

## File Changes

### Modify Files

**1. `app/repository/permission_repository.py`** — Add get_by_id
```python
async def get_by_id(self, permission_id: int) -> Permission | None:
    result = await self.session.execute(
        select(Permission).where(Permission.id == permission_id)
    )
    return result.scalar_one_or_none()
```

**2. `app/service/permission_service.py`** — Add get method
```python
async def get_permission(self, permission_id: int) -> PermissionEntity:
    perm = await self.repo.get_by_id(permission_id)
    if not perm:
        raise ValueError("Permission not found")
    return PermissionEntity.model_validate(perm)
```

**3. `app/api/v1/endpoints/permissions.py`** — Add get endpoint
```python
@router.get("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:read"])),
):
    service = PermissionService(db)
    perm = await service.get_permission(permission_id)
    return ApiResponse(data=PermissionResponse.model_validate(perm))
```

## Verification

- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Test: `GET /api/v1/permissions/1` → returns permission
- Test: `GET /api/v1/permissions/9999` → returns 404 error via ValueError