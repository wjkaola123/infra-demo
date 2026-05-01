import pytest
from httpx import AsyncClient
import time


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """Test creating a new user."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@test.com"
    }
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["username"] == user_data["username"]
    assert data["data"]["email"] == user_data["email"]
    assert data["data"]["is_active"] is True
    assert "id" in data["data"]
    assert "created_at" in data["data"]


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient):
    """Test getting a single user."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"getuser_{timestamp}",
        "email": f"getuser_{timestamp}@test.com"
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Then get the user
    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["id"] == user_id
    assert data["data"]["username"] == user_data["username"]
    assert data["data"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """Test listing all users."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"listuser_{timestamp}",
        "email": f"listuser_{timestamp}@test.com"
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    created_id = create_response.json()["data"]["id"]

    # List all users
    response = await client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert isinstance(data["data"], list)
    # Verify created user is in the list
    usernames = [u["username"] for u in data["data"]]
    assert user_data["username"] in usernames


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    """Test updating a user."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"updateuser_{timestamp}",
        "email": f"updateuser_{timestamp}@test.com"
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Update the user
    update_data = {"username": f"updated_{timestamp}"}
    response = await client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["id"] == user_id
    assert data["data"]["username"] == update_data["username"]
    assert data["data"]["email"] == user_data["email"]
    assert data["data"]["updated_at"] is not None


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    """Test deleting a user."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"deleteuser_{timestamp}",
        "email": f"deleteuser_{timestamp}@test.com"
    }
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Delete the user
    response = await client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["id"] == user_id

    # Verify user is deleted
    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404