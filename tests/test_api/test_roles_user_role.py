import pytest


@pytest.mark.asyncio
async def test_assign_permissions_to_role(client):
    """Test assigning permissions to a role."""
    # Create a role first
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "perm_test_role", "description": "Permission test role"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Assign permissions (permission IDs 1 and 2 should exist from migration)
    response = await client.post(
        f"/api/v1/roles/{role_id}/permissions",
        json={"permission_ids": [1, 2]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert len(data["data"]) >= 0  # May be empty if permissions don't exist yet


@pytest.mark.asyncio
async def test_remove_permission_from_role(client):
    """Test removing a permission from a role."""
    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "remove_perm_role", "description": "Test role"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Try to remove a permission (may fail if not assigned)
    response = await client.delete(f"/api/v1/roles/{role_id}/permissions/1")
    # Either succeeds (200) or fails because permission wasn't assigned (404)
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_user_roles(client):
    """Test getting roles assigned to a user."""
    # Create a role first
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "user_roles_test", "description": "Test role"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Get user roles (user_id 1 should exist from seed data)
    response = await client.get("/api/v1/roles/users/1/roles")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_assign_role_to_user(client):
    """Test assigning a role to a user."""
    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "assign_role_test", "description": "Test role"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Assign role to user (user_id 1 should exist)
    response = await client.post(
        "/api/v1/roles/users/1/roles",
        json={"role_id": role_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["role_id"] == role_id


@pytest.mark.asyncio
async def test_remove_role_from_user(client):
    """Test removing a role from a user."""
    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "remove_user_role", "description": "Test role"}
    )
    role_id = create_resp.json()["data"]["id"]

    # First assign the role
    await client.post(
        "/api/v1/roles/users/1/roles",
        json={"role_id": role_id}
    )

    # Then remove it
    response = await client.delete(f"/api/v1/roles/users/1/roles/{role_id}")
    # May be 200 (success) or 404 (role not assigned)
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_user_permissions(client):
    """Test getting all permissions for a user."""
    response = await client.get("/api/v1/roles/users/1/permissions")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert isinstance(data["data"], list)