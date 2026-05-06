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

## Tests

```python
@pytest.mark.asyncio
async def test_update_permission(client: AsyncClient, db_session):
    """Test updating a permission's name and description."""
    token = await get_admin_token(client, db_session, "updateperm")
    timestamp = int(time.time() * 1000)

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"to_update_{timestamp}", "description": "Original desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": f"updated_name_{timestamp}", "description": "Updated desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["data"]["name"] == f"updated_name_{timestamp}"
    assert data["data"]["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_update_permission_partial_update(client: AsyncClient, db_session):
    """Test partial update - only name."""
    token = await get_admin_token(client, db_session, "partialperm")
    timestamp = int(time.time() * 1000)

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"partial_{timestamp}", "description": "Original"},
        headers={"Authorization": f"Bearer {token}"}
    )
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": f"partial_updated_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == f"partial_updated_{timestamp}"
    assert data["data"]["description"] == "Original"


@pytest.mark.asyncio
async def test_update_permission_not_found(client: AsyncClient, db_session):
    """Test updating non-existent permission returns 404."""
    token = await get_admin_token(client, db_session, "updatenotfound")

    response = await client.put(
        "/api/v1/permissions/99999",
        json={"name": "some:name"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_permission_duplicate_name(client: AsyncClient, db_session):
    """Test updating permission with duplicate name returns 400."""
    token = await get_admin_token(client, db_session, "dupnameperm")
    timestamp = int(time.time() * 1000)

    await client.post(
        "/api/v1/permissions/",
        json={"name": f"existing_{timestamp}", "description": "First"},
        headers={"Authorization": f"Bearer {token}"}
    )

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"to_update_{timestamp}", "description": "Second"},
        headers={"Authorization": f"Bearer {token}"}
    )
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": f"existing_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_permission_invalid_name_format(client: AsyncClient, db_session):
    """Test updating permission with invalid name format returns 422."""
    token = await get_admin_token(client, db_session, "invalidup")
    timestamp = int(time.time() * 1000)

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"valid_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": "InvalidName"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_permission_requires_auth(client: AsyncClient):
    """Test that updating permission requires authentication."""
    response = await client.put(
        "/api/v1/permissions/1",
        json={"name": "some:name"}
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_permission_requires_write_permission(client: AsyncClient, db_session):
    """Test that updating permission requires permissions:write."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"updatenoperm_{timestamp}",
        "email": f"updatenoperm_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token = register_response.json()["data"]["access_token"]

    response = await client.put(
        "/api/v1/permissions/1",
        json={"name": f"some:name_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
```

## Verification

- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Run: `docker-compose exec api python -m pytest tests/test_api/test_permissions.py -v`
- Update existing permission → 200
- Update with duplicate name → 400
- Update non-existent → 404
- Update with invalid name format → 422
- No auth → 401/403
- No `permissions:write` permission → 403