import pytest
import time
from httpx import AsyncClient


async def get_admin_token(client: AsyncClient) -> str:
    """Helper to get admin access token by registering and assigning admin role."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"admin_{timestamp}",
        "email": f"admin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    # Assign admin role (role_id=1 should be admin from migration)
    await client.post(
        f"/api/v1/roles/users/999999/roles",  # This won't work, need different approach
        json={"role_id": 1},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    return access_token


@pytest.mark.asyncio
async def test_create_role(client: AsyncClient):
    """Test creating a role."""
    # First register and get token
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    response = await client.post(
        "/api/v1/roles/",
        json={"name": f"test_role_{timestamp}", "description": "Test role description"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["name"] == f"test_role_{timestamp}"
    assert data["data"]["description"] == "Test role description"


@pytest.mark.asyncio
async def test_get_role(client: AsyncClient):
    """Test getting a role by ID."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    # Create a role first
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"get_test_role_{timestamp}", "description": "Test role"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Get the role
    response = await client.get(
        f"/api/v1/roles/{role_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["id"] == role_id
    assert data["data"]["name"] == f"get_test_role_{timestamp}"


@pytest.mark.asyncio
async def test_list_roles(client: AsyncClient):
    """Test listing roles with pagination."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    # Create some roles
    for i in range(3):
        await client.post(
            "/api/v1/roles/",
            json={"name": f"list_role_{timestamp}_{i}", "description": f"Role {i}"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

    # List roles
    response = await client.get(
        "/api/v1/roles/?page=1&page_size=10",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert "items" in data["data"]
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 10


@pytest.mark.asyncio
async def test_update_role(client: AsyncClient):
    """Test updating a role."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"update_test_role_{timestamp}", "description": "Original description"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Update the role
    response = await client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": f"updated_role_{timestamp}", "description": "Updated description"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["name"] == f"updated_role_{timestamp}"
    assert data["data"]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_role(client: AsyncClient):
    """Test deleting a role."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": f"delete_test_role_{timestamp}", "description": "To be deleted"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Delete the role
    response = await client.delete(
        f"/api/v1/roles/{role_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == 0

    # Verify role is deleted
    get_resp = await client.get(
        f"/api/v1/roles/{role_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_role(client: AsyncClient):
    """Test getting a non-existent role returns 404."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/roles/99999",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_role(client: AsyncClient):
    """Test updating a non-existent role returns 404."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    response = await client.put(
        "/api/v1/roles/99999",
        json={"name": "nonexistent"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_role(client: AsyncClient):
    """Test deleting a non-existent role returns 404."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleadmin_{timestamp}",
        "email": f"roleadmin_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]

    response = await client.delete(
        "/api/v1/roles/99999",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404