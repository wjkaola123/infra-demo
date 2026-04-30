import pytest
from httpx import AsyncClient


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
    user_data = {
        "username": "testuser",
        "email": "test@example.com"
    }
    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_duplicate_user(client: AsyncClient):
    """Test creating a user with duplicate username."""
    user_data = {
        "username": "duplicate",
        "email": "duplicate@example.com"
    }
    # Create first user
    response1 = await client.post("/api/v1/users", json=user_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await client.post("/api/v1/users", json=user_data)
    assert response2.status_code == 400
