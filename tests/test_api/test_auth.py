import pytest
import time
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"reguser_{timestamp}",
        "email": f"reguser_{timestamp}@test.com",
        "password": "password123"
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """Test registration with duplicate username."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"dupuser_{timestamp}",
        "email": f"dupuser_{timestamp}@test.com",
        "password": "password123"
    }
    # First registration
    await client.post("/api/v1/auth/register", json=user_data)
    # Second registration with same username
    user_data["email"] = f"different_{timestamp}@test.com"
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"dupemail_{timestamp}",
        "email": f"dupemail_{timestamp}@test.com",
        "password": "password123"
    }
    # First registration
    await client.post("/api/v1/auth/register", json=user_data)
    # Second registration with same email
    user_data["username"] = f"different_{timestamp}"
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"loginuser_{timestamp}",
        "email": f"loginuser_{timestamp}@test.com",
        "password": "password123"
    }
    # Register first
    await client.post("/api/v1/auth/register", json=user_data)
    # Then login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with wrong password."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"loginwrong_{timestamp}",
        "email": f"loginwrong_{timestamp}@test.com",
        "password": "correctpassword"
    }
    # Register first
    await client.post("/api/v1/auth/register", json=user_data)
    # Login with wrong password
    login_data = {
        "username": user_data["username"],
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user."""
    login_data = {
        "username": "nonexistent_user_12345",
        "password": "password123"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    """Test successful token refresh."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"refreshuser_{timestamp}",
        "email": f"refreshuser_{timestamp}@test.com",
        "password": "password123"
    }
    # Register first
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    refresh_token = register_response.json()["data"]["refresh_token"]
    # Refresh token
    refresh_data = {"refresh_token": refresh_token}
    response = await client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Test refresh with invalid token."""
    refresh_data = {"refresh_token": "invalid_token_here"}
    response = await client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_register_invalid_email_format(client: AsyncClient):
    """Test registration with invalid email format."""
    user_data = {
        "username": "testuser",
        "email": "not-an-email",
        "password": "password123"
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 422  # Validation error