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


@pytest.mark.asyncio
async def test_list_permissions(client: AsyncClient, db_session):
    """Test listing permissions with pagination."""
    token = await get_admin_token(client, db_session, "listperm")

    response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert "page" in data["data"]
    assert "page_size" in data["data"]
    assert "total_pages" in data["data"]
    assert isinstance(data["data"]["items"], list)
    for perm in data["data"]["items"]:
        assert "id" in perm
        assert "name" in perm
        assert "description" in perm


@pytest.mark.asyncio
async def test_list_permissions_with_pagination(client: AsyncClient, db_session):
    """Test listing permissions with pagination params."""
    token = await get_admin_token(client, db_session, "listpage")

    response = await client.get(
        "/api/v1/permissions/?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 5
    assert len(data["data"]["items"]) <= 5


@pytest.mark.asyncio
async def test_list_permissions_filter_by_name(client: AsyncClient, db_session):
    """Test filtering permissions by name returns case-insensitive partial matches."""
    token = await get_admin_token(client, db_session, "filterperm")

    response = await client.get(
        "/api/v1/permissions/?name=permissions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    # Should return permissions containing "permissions" in name (permissions:read, permissions:write, etc.)
    assert len(data["data"]["items"]) >= 3
    names = [p["name"] for p in data["data"]["items"]]
    assert "permissions:read" in names
    assert "permissions:write" in names
    assert "permissions:delete" in names


@pytest.mark.asyncio
async def test_list_permissions_requires_auth(client: AsyncClient):
    """Test that listing permissions requires authentication."""
    response = await client.get("/api/v1/permissions/")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_list_permissions_requires_read_permission(client: AsyncClient, db_session):
    """Test that listing permissions requires permissions:read."""
    from sqlalchemy import text
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"listnoread_{timestamp}",
        "email": f"listnoread_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token = register_response.json()["data"]["access_token"]
    user_name = register_response.json()["data"]["username"]

    result = await db_session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user_name}
    )
    user_id = result.scalar_one()

    # Assign viewer role (only has users:read, not permissions:read)
    result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'viewer'"))
    viewer_id = result.scalar_one()
    await db_session.execute(
        text("DELETE FROM user_roles WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    await db_session.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
        {"user_id": user_id, "role_id": viewer_id}
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/permissions/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_permission(client: AsyncClient, db_session):
    """Test getting a permission by ID."""
    token = await get_admin_token(client, db_session, "getperm")
    timestamp = int(time.time() * 1000)

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"get:test_{timestamp}", "description": "Test permission"},
        headers={"Authorization": f"Bearer {token}"}
    )
    perm_id = create_response.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["status"] == 0
    assert data["data"]["id"] == perm_id
    assert data["data"]["name"] == f"get:test_{timestamp}"
    assert data["data"]["description"] == "Test permission"
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]


@pytest.mark.asyncio
async def test_get_permission_not_found(client: AsyncClient, db_session):
    """Test getting a non-existent permission returns 404."""
    token = await get_admin_token(client, db_session, "notfoundperm")

    response = await client.get(
        "/api/v1/permissions/999999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_permission_requires_auth(client: AsyncClient):
    """Test that getting permission by ID requires authentication."""
    response = await client.get("/api/v1/permissions/1")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_permission_requires_read_permission(client: AsyncClient, db_session):
    """Test that getting permission by ID requires permissions:read."""
    from sqlalchemy import text
    timestamp = int(time.time() * 1000)
    user_data = {
        "username": f"getnoread_{timestamp}",
        "email": f"getnoread_{timestamp}@test.com",
        "password": "password123"
    }
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    token = register_response.json()["data"]["access_token"]
    user_name = register_response.json()["data"]["username"]

    result = await db_session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {"username": user_name}
    )
    user_id = result.scalar_one()

    result = await db_session.execute(text("SELECT id FROM roles WHERE name = 'viewer'"))
    viewer_id = result.scalar_one()
    await db_session.execute(
        text("DELETE FROM user_roles WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    await db_session.execute(
        text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"),
        {"user_id": user_id, "role_id": viewer_id}
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/permissions/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_permission(client: AsyncClient, db_session):
    """Test updating a permission's name and description."""
    token = await get_admin_token(client, db_session, "updateperm")
    timestamp = int(time.time() * 1000)

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"test:update_{timestamp}", "description": "Original desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 201
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": f"test:updated_{timestamp}", "description": "Updated desc"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "success"
    assert data["data"]["name"] == f"test:updated_{timestamp}"
    assert data["data"]["description"] == "Updated desc"


@pytest.mark.asyncio
async def test_update_permission_partial_update(client: AsyncClient, db_session):
    """Test partial update - only name."""
    token = await get_admin_token(client, db_session, "partialperm")
    timestamp = int(time.time() * 1000)

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"test:partial_{timestamp}", "description": "Original"},
        headers={"Authorization": f"Bearer {token}"}
    )
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": f"test:partial_updated_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == f"test:partial_updated_{timestamp}"
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
        json={"name": f"test:existing_{timestamp}", "description": "First"},
        headers={"Authorization": f"Bearer {token}"}
    )

    create_response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"test:to_update_{timestamp}", "description": "Second"},
        headers={"Authorization": f"Bearer {token}"}
    )
    perm_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/permissions/{perm_id}",
        json={"name": f"test:existing_{timestamp}"},
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
        json={"name": f"test:valid_{timestamp}"},
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
        json={"name": f"test:some_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_permission(client: AsyncClient, db_session):
    """Test deleting a permission."""
    token = await get_admin_token(client, db_session, "delperm")
    timestamp = int(time.time() * 1000)

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"delperm:delete_{timestamp}", "description": "Will be deleted"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    perm_id = response.json()["data"]["id"]

    delete_resp = await client.delete(
        f"/api/v1/permissions/{perm_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["deleted"] is True

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
    from sqlalchemy import text
    token = await get_admin_token(client, db_session, "delpermassigned")
    timestamp = int(time.time() * 1000)

    response = await client.post(
        "/api/v1/permissions/",
        json={"name": f"delpermassigned:delete_{timestamp}"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    perm_id = response.json()["data"]["id"]

    await db_session.execute(
        text("INSERT INTO role_permissions (role_id, permission_id) VALUES (1, :perm_id)"),
        {"perm_id": perm_id}
    )
    await db_session.commit()

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

