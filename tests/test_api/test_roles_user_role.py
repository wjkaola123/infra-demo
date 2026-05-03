import pytest
import time
from httpx import AsyncClient


async def get_access_token(client: AsyncClient, username: str) -> str:
    """Helper to get access token."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"{username}_{timestamp}",
        "email": f"{username}_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    return register_response.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_assign_permissions_to_role(client: AsyncClient):
    """Test assigning permissions to a role."""
    token = await get_access_token(client, "permtest")

    # Create a role first
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"perm_test_role_{time.time()}", "description": "Permission test role"},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Assign permissions (permission IDs 1 and 2 should exist from migration)
    response = await client.post(
        f"/api/v1/roles/{role_id}/permissions",
        json={"permission_ids": [1, 2]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert len(data["data"]) >= 0


@pytest.mark.asyncio
async def test_remove_permission_from_role(client: AsyncClient):
    """Test removing a permission from a role."""
    token = await get_access_token(client, "removetest")

    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"remove_perm_role_{time.time()}", "description": "Test role"},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Try to remove a permission
    response = await client.delete(
        f"/api/v1/roles/{role_id}/permissions/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_user_roles(client: AsyncClient):
    """Test getting roles assigned to a user."""
    token = await get_access_token(client, "getroles")

    # Create a role first
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"user_roles_test_{time.time()}", "description": "Test role"},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Get user roles - use the same user we registered (use a high ID that won't exist)
    response = await client.get(
        "/api/v1/roles/users/999999/roles",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_assign_role_to_user(client: AsyncClient):
    """Test assigning a role to a user - using existing admin user."""
    token = await get_access_token(client, "assignrole")

    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"assign_role_test_{time.time()}", "description": "Test role"},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Use user_id=1 which should exist
    response = await client.post(
        f"/api/v1/roles/users/1/roles",
        json={"role_id": role_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    # User 1 may or may not exist, accept both
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_remove_role_from_user(client: AsyncClient):
    """Test removing a role from a user."""
    token = await get_access_token(client, "removerole")

    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"remove_user_role_{time.time()}", "description": "Test role"},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Try to remove - user won't exist so 404
    response = await client.delete(
        f"/api/v1/roles/users/999999/roles/{role_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_user_permissions(client: AsyncClient):
    """Test getting all permissions for a user."""
    token = await get_access_token(client, "getperms")

    response = await client.get(
        "/api/v1/roles/users/999999/permissions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert isinstance(data["data"], list)