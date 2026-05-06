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

**3. `app/service/permission_service.py`** — Add update method (DDD: ORM → Domain Entity)
```python
async def update_permission(self, permission_id: int, name: str | None, description: str | None) -> PermissionEntity:
    if name is not None:
        existing = await self.repo.get_by_name(name)
        if existing and existing.id != permission_id:
            raise ValueError("Permission name already exists")
    perm = await self.repo.update(permission_id, name, description)
    if not perm:
        raise ValueError("Permission not found")
    return PermissionEntity(
        id=perm.id,
        name=perm.name,
        description=perm.description,
        created_at=perm.created_at,
        updated_at=perm.updated_at,
    )
```

**4. `app/api/v1/endpoints/permissions.py`** — Add update endpoint (DDD: Domain Entity → Response DTO)
```python
@router.put("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def update_permission(
    permission_id: int,
    body: UpdatePermissionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:write"])),
):
    service = PermissionService(db)
    try:
        entity = await service.update_permission(permission_id, body.name, body.description)
    except ValueError as e:
        detail = str(e).lower()
        if "not found" in detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ApiResponse(data=PermissionResponse(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    ))
```

## Data Flow (DDD)

```
DB (permissions table)
  ↓ ORM: UPDATE + commit + refresh
Repository: update()
  ↓ Conversion: Permission → PermissionEntity
Service: update_permission() → PermissionEntity
  ↓ Conversion: PermissionEntity → PermissionResponse
Endpoint
  ↓
API Response (JSON)
```

## Verification

- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Test: `PUT /api/v1/permissions/1` with `{"name": "articles:write", "description": "Updated desc"}`
- Duplicate name: should return 400 error
- Non-existent ID: should return 404 error