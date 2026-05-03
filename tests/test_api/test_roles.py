import pytest


@pytest.mark.asyncio
async def test_create_role(client):
    """Test creating a role."""
    response = await client.post(
        "/api/v1/roles/",
        json={"name": "test_role", "description": "Test role description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["name"] == "test_role"
    assert data["data"]["description"] == "Test role description"


@pytest.mark.asyncio
async def test_get_role(client):
    """Test getting a role by ID."""
    # Create a role first
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "get_test_role", "description": "Test role"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Get the role
    response = await client.get(f"/api/v1/roles/{role_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["id"] == role_id
    assert data["data"]["name"] == "get_test_role"


@pytest.mark.asyncio
async def test_list_roles(client):
    """Test listing roles with pagination."""
    # Create some roles
    for i in range(3):
        await client.post(
            "/api/v1/roles/",
            json={"name": f"list_role_{i}", "description": f"Role {i}"}
        )

    # List roles
    response = await client.get("/api/v1/roles/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert "items" in data["data"]
    assert data["data"]["total"] >= 3
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 10


@pytest.mark.asyncio
async def test_update_role(client):
    """Test updating a role."""
    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "update_test_role", "description": "Original description"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Update the role
    response = await client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": "updated_role", "description": "Updated description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 0
    assert data["data"]["name"] == "updated_role"
    assert data["data"]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_role(client):
    """Test deleting a role."""
    # Create a role
    create_resp = await client.post(
        "/api/v1/roles/",
        json={"name": "delete_test_role", "description": "To be deleted"}
    )
    role_id = create_resp.json()["data"]["id"]

    # Delete the role
    response = await client.delete(f"/api/v1/roles/{role_id}")
    assert response.status_code == 200
    assert response.json()["status"] == 0

    # Verify role is deleted
    get_resp = await client.get(f"/api/v1/roles/{role_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_nonexistent_role(client):
    """Test getting a non-existent role returns 404."""
    response = await client.get("/api/v1/roles/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_role(client):
    """Test updating a non-existent role returns 404."""
    response = await client.put(
        "/api/v1/roles/99999",
        json={"name": "nonexistent"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_role(client):
    """Test deleting a non-existent role returns 404."""
    response = await client.delete("/api/v1/roles/99999")
    assert response.status_code == 404