# Plan: Delete Permission API

## Context

Adding `DELETE /api/v1/permissions/{id}` endpoint to delete a permission. Only used permissions (assigned to any role) cannot be deleted — the API returns 409 Conflict.

## Prerequisite

**Run migration `004` first** — `permissions:delete` must exist and be assigned to admin role before implementing this endpoint, otherwise the endpoint will always return 403 for admin users.

```bash
docker-compose exec api python -m alembic upgrade head
```

## API Contract

```
DELETE /api/v1/permissions/{id}
Authorization: Bearer <access_token>

Success Response (200 OK):
{
  "message": "success",
  "status": 0,
  "data": {"deleted": true}
}

Error Responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: User lacks `permissions:delete` permission
- 404 Not Found: Permission does not exist
- 409 Conflict: Permission is assigned to one or more roles
  {"detail": "Permission is assigned to roles and cannot be deleted"}
```

## File Changes

### New Files (0)

### Modified Files (2)

**1. `app/repository/permission_repository.py`** — Add delete and usage-check methods
```python
async def get_by_id(self, permission_id: int) -> Permission | None:
    result = await self.session.execute(
        select(Permission).where(Permission.id == permission_id)
    )
    return result.scalar_one_or_none()

async def is_assigned_to_roles(self, permission_id: int) -> bool:
    result = await self.session.execute(
        select(role_permissions).where(
            role_permissions.c.permission_id == permission_id
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None

async def delete(self, permission_id: int) -> bool:
    permission = await self.get_by_id(permission_id)
    if not permission:
        return False
    await self.session.delete(permission)
    await self.session.commit()
    return True
```

**2. `app/service/permission_service.py`** — Add delete_permission method
```python
async def delete_permission(self, permission_id: int) -> bool:
    existing = await self.repo.get_by_id(permission_id)
    if not existing:
        raise ValueError("Permission not found")
    if await self.repo.is_assigned_to_roles(permission_id):
        raise ValueError("Permission is assigned to roles and cannot be deleted")
    return await self.repo.delete(permission_id)
```

**3. `app/api/v1/endpoints/permissions.py`** — Add delete endpoint
```python
from fastapi import APIRouter, Depends, Path, HTTPException, status
from app.repository.entity.user import User

@router.delete("/{permission_id}", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
async def delete_permission(
    permission_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:delete"])),
):
    service = PermissionService(db)
    try:
        deleted = await service.delete_permission(permission_id)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    return ApiResponse(data={"deleted": deleted})
```

## Tests

```python
@pytest.mark.asyncio
async def test_delete_permission(client: AsyncClient, db_session):
    """Test deleting a permission."""
    token = await get_admin_token(client, db_session, "delperm")
    timestamp = int(time.time() * 1000)

    # Create a permission (admin has permissions:write, which covers delete need in test)
    # Actually need permissions:delete - use admin role which has all
    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"to_delete_{timestamp}", "description": "Will be deleted"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    perm_id = response.json()["data"]["id"]

    # Delete it
    delete_resp = await client.delete(
        f"/api/v1/permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["deleted"] is True

    # Verify gone
    get_resp = await client.get(
        f"/api/v1/permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_permission_not_found(client: AsyncClient, db_session):
    """Test deleting non-existent permission returns 404."""
    token = await get_admin_token(client, db_session, "delpermnotfound")

    response = await client.delete(
        "/api/v1/permissions/99999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_permission_assigned_to_role(client: AsyncClient, db_session):
    """Test deleting a permission assigned to a role returns 409."""
    token = await get_admin_token(client, db_session, "delpermassigned")
    timestamp = int(time.time() * 1000)

    # Create permission
    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"assigned_perm_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    perm_id = response.json()["data"]["id"]

    # Assign it to admin role (role id 1)
    await db_session.execute(
        text("INSERT INTO role_permissions (role_id, permission_id) VALUES (1, :perm_id)"),
        {"perm_id": perm_id}
    )
    await db_session.commit()

    # Try to delete - should fail 409
    delete_resp = await client.delete(
        f"/api/v1/permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 409


@pytest.mark.asyncio
async def test_delete_permission_requires_auth(client: AsyncClient):
    """Test that deleting permission requires authentication."""
    response = await client.delete("/api/v1/permissions/1")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_delete_permission_requires_delete_permission(client: AsyncClient, db_session):
    """Test that deleting permission requires permissions:delete."""
    # Create user without permissions:delete
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"odelete_{timestamp}",
        "email": f"odelete_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token = register_response.json()["data"]["access_token"]

    response = await client.delete(
        "/api/v1/permissions/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
```

## Verification
- Run migration first: `docker-compose exec api python -m alembic upgrade head`
- Run: `docker-compose exec api python -m pytest tests/ -v`
- Run: `docker-compose exec api python -m pytest tests/test_api/test_permissions.py -v`
- Delete existing permission → 200, `{"deleted": true}`
- Delete non-existent → 404
- Delete permission assigned to role → 409
- No auth → 401/403
- No `permissions:delete` permission → 403
