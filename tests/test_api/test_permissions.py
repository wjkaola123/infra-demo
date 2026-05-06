import pytest
import time
from httpx import AsyncClient


async def get_admin_token(client: AsyncClient, db_session, username: str) -> str:
    """Helper to get admin access token with permissions:write."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"{username}_{timestamp}",
        "email": f"{username}_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    access_token = register_response.json()["data"]["access_token"]
    user_name = register_response.json()["data"]["username"]

    from sqlalchemy import text
    result = await db_session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user_name}
    )
    user_id = result.scalar_one()

    await db_session.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, 1)"),
        {"user_id": user_id}
    )
    await db_session.commit()
    return access_token


@pytest.mark.asyncio
async def test_create_permission(client: AsyncClient, db_session):
    """Test creating a new permission."""
    token = await get_admin_token(client, db_session, "createperm")
    timestamp = int(time.time() * 1000)

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"articles:read_{timestamp}", "description": "Read articles"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["name"] == f"articles:read_{timestamp}"
    assert data["data"]["description"] == "Read articles"
    assert "id" in data["data"]
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]


@pytest.mark.asyncio
async def test_create_permission_duplicate_name(client: AsyncClient, db_session):
    """Test creating a permission with duplicate name returns 400."""
    token = await get_admin_token(client, db_session, "dupperm")
    timestamp = int(time.time() * 1000)
    perm_name = f"dup:test_{timestamp}"

    await client.post(
        "/api/v1/permissions/",
        json={"name": perm_name, "description": "First"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": perm_name, "description": "Duplicate"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_permission_invalid_name_format(client: AsyncClient, db_session):
    """Test creating a permission with invalid name format returns 422."""
    token = await get_admin_token(client, db_session, "invperm")

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": "InvalidName", "description": "Bad format"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_permission_requires_auth(client: AsyncClient):
    """Test that creating permission requires authentication."""
    response = await client.post(
        "/api/v1/permissions/",
        json={"name": "test:auth", "description": "Test"}
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_permission_requires_write_permission(client: AsyncClient, db_session):
    """Test that creating permission requires permissions:write."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"nowrite_{timestamp}",
        "email": f"nowrite_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token = register_response.json()["data"]["access_token"]

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"test:noperm_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


