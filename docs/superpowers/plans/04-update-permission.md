# Plan: Update Permission API

## Context

Adding `PUT /api/v1/permissions/{id}` endpoint to update name and/or description of a permission.

## Prerequisite

**Run migration `004` first** — `permissions:write` must exist and be assigned to admin role before implementing this endpoint.

```bash
docker-compose exec api python -m alembic upgrade head
```

## File Changes

### Modify Files

**1. `app/handler/entity/request/permission.py`** — Add UpdatePermissionRequest
```python
class UpdatePermissionRequest(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-z0-9_]+:[a-z0-9_]+$", v):
            raise ValueError("Format must be 'resource:action' with lowercase letters, numbers, underscores")
        return v
```

**2. `app/repository/permission_repository.py`** — Add update method
```python
async def update(self, permission_id: int, name: str | None = None, description: str | None = None) -> Permission | None:
    perm = await self.get_by_id(permission_id)
    if not perm:
        return None
    if name is not None:
        perm.name = name
    if description is not None:
        perm.description = description
    await self.session.commit()
    await self.session.refresh(perm)
    return perm
```

**3. `app/service/permission_service.py`** — Add update method
```python
async def update_permission(self, permission_id: int, name: str | None, description: str | None) -> PermissionEntity:
    if name is not None:
        existing = await self.repo.get_by_name(name)
        if existing and existing.id != permission_id:
            raise ValueError("Permission name already exists")
    perm = await self.repo.update(permission_id, name, description)
    if not perm:
        raise ValueError("Permission not found")
    return PermissionEntity.model_validate(perm)
```

**4. `app/api/v1/endpoints/permissions.py`** — Add update endpoint
```python
@router.put("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def update_permission(
    permission_id: int,
    body: UpdatePermissionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:write"])),
):
    service = PermissionService(db)
    perm = await service.update_permission(permission_id, body.name, body.description)
    return ApiResponse(data=PermissionResponse.model_validate(perm))
```

## Verification

- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Test: `PUT /api/v1/permissions/1` with `{"name": "articles:write", "description": "Updated desc"}`
- Duplicate name: should return 400 error
- Non-existent ID: should return 404 error