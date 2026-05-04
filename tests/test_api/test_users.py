import pytest
from httpx import AsyncClient
import time


async def get_access_token(client: AsyncClient, username: str) -> str:
    """Helper to get access token by registering and logging in."""
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"{username}_{timestamp}",
        "email": f"{username}_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    return register_response.json()["data"]["access_token"]


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
    token = await get_access_token(client, "testuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@test.com"
    }
    response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
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
    token = await get_access_token(client, "getuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"getuser_{timestamp}",
        "email": f"getuser_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Then get the user
    response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["id"] == user_id
    assert data["data"]["username"] == user_data["username"]
    assert data["data"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """Test listing users with pagination."""
    token = await get_access_token(client, "listuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"listuser_{timestamp}",
        "email": f"listuser_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201

    # List users with pagination - verify structure
    response = await client.get(
        "/api/v1/users/?page=1&page_size=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
    assert "page_size" in data["data"]
    assert "total_pages" in data["data"]
    assert isinstance(data["data"]["items"], list)
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 10
    # Total should be at least the number of users we've created
    assert data["data"]["total"] >= 1
    # Items should be users
    assert len(data["data"]["items"]) <= 10

    # Get the last page to verify our created user exists
    total_pages = data["data"]["total_pages"]
    last_page_response = await client.get(
        f"/api/v1/users/?page={total_pages}&page_size=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    last_page_data = last_page_response.json()["data"]
    last_page_usernames = [u["username"] for u in last_page_data["items"]]
    assert user_data["username"] in last_page_usernames


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    """Test updating a user."""
    token = await get_access_token(client, "updateuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"updateuser_{timestamp}",
        "email": f"updateuser_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Update the user
    update_data = {"username": f"updated_{timestamp}"}
    response = await client.put(
        f"/api/v1/users/{user_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["id"] == user_id
    assert data["data"]["username"] == update_data["username"]
    assert data["data"]["email"] == user_data["email"]
    assert data["data"]["updated_at"] is not None


@pytest.mark.asyncio
async def test_update_user_assign_roles(client: AsyncClient, db_session):
    """Test assigning roles to a user via PUT /users/{id}."""
    from sqlalchemy import text
    from tests.test_api.test_roles import get_admin_token
    token = await get_admin_token(client, db_session, "assignroleuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleassign_{timestamp}",
        "email": f"roleassign_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Create two roles to assign
    role1_response = await client.post(
        "/api/v1/roles/",
        json={"name": f"test_role_a_{timestamp}", "description": "Test A", "permission_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    role2_response = await client.post(
        "/api/v1/roles/",
        json={"name": f"test_role_b_{timestamp}", "description": "Test B", "permission_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    role1_id = role1_response.json()["data"]["id"]
    role2_id = role2_response.json()["data"]["id"]

    # Assign roles via update endpoint
    update_response = await client.put(
        f"/api/v1/users/{user_id}",
        json={"role_ids": [role1_id, role2_id]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200

    # Verify roles were assigned via direct DB query
    result = await db_session.execute(
        text("SELECT role_id FROM user_roles WHERE user_id = :user_id ORDER BY role_id"),
        {"user_id": user_id}
    )
    assigned_role_ids = [row[0] for row in result.all()]
    assert role1_id in assigned_role_ids
    assert role2_id in assigned_role_ids


@pytest.mark.asyncio
async def test_update_user_clear_roles(client: AsyncClient, db_session):
    """Test clearing all roles from a user via PUT /users/{id} with empty role_ids."""
    from sqlalchemy import text
    from tests.test_api.test_roles import get_admin_token
    token = await get_admin_token(client, db_session, "clearroleuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"roleclear_{timestamp}",
        "email": f"roleclear_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Create and assign a role
    role_response = await client.post(
        "/api/v1/roles/",
        json={"name": f"role_to_clear_{timestamp}", "description": "Test", "permission_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = role_response.json()["data"]["id"]
    await client.post(
        f"/api/v1/roles/users/{user_id}/roles",
        json={"role_id": role_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify role is assigned
    result = await db_session.execute(
        text("SELECT role_id FROM user_roles WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    assert result.scalar_one_or_none() is not None

    # Clear roles via update endpoint with empty list
    update_response = await client.put(
        f"/api/v1/users/{user_id}",
        json={"role_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200

    # Verify roles were cleared
    result = await db_session.execute(
        text("SELECT role_id FROM user_roles WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_update_user_invalid_role_ids(client: AsyncClient, db_session):
    """Test that assigning non-existent role IDs returns 400."""
    from tests.test_api.test_roles import get_admin_token
    token = await get_admin_token(client, db_session, "invalidroleuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"invalidrole_{timestamp}",
        "email": f"invalidrole_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Try to assign non-existent role IDs
    update_response = await client.put(
        f"/api/v1/users/{user_id}",
        json={"role_ids": [99999, 88888]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 400


@pytest.mark.asyncio
async def test_update_user_preserve_roles_without_role_ids_field(client: AsyncClient, db_session):
    """Test that omitting role_ids preserves existing roles."""
    from sqlalchemy import text
    from tests.test_api.test_roles import get_admin_token
    token = await get_admin_token(client, db_session, "preserveroleuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"preserveroles_{timestamp}",
        "email": f"preserveroles_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Assign a role
    role_response = await client.post(
        "/api/v1/roles/",
        json={"name": f"preserve_role_{timestamp}", "description": "Test", "permission_ids": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    role_id = role_response.json()["data"]["id"]
    await client.post(
        f"/api/v1/roles/users/{user_id}/roles",
        json={"role_id": role_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Update only email, without providing role_ids
    update_response = await client.put(
        f"/api/v1/users/{user_id}",
        json={"email": f"new_{timestamp}@test.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["email"] == f"new_{timestamp}@test.com"

    # Verify role is still assigned
    result = await db_session.execute(
        text("SELECT role_id FROM user_roles WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    assert result.scalar_one_or_none() == role_id


@pytest.mark.asyncio
async def test_delete_user_no_permission(client: AsyncClient):
    """Test that non-admin user cannot delete users."""
    token = await get_access_token(client, "deleteuser")
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"deleteuser_{timestamp}",
        "email": f"deleteuser_{timestamp}@test.com"
    }
    create_response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["data"]["id"]

    # Editor role doesn't have users:delete permission, should get 403
    response = await client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403