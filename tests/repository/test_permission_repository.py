import pytest
import time
from app.repository.permission_repository import PermissionRepository
from app.repository.role_repository import RoleRepository
from app.repository.entity.role import Role


@pytest.mark.asyncio
async def test_create(db_session):
    """Test creating a permission."""
    repository = PermissionRepository(db_session)
    name = f"test_perm_{int(time.time() * 1000)}"
    perm = await repository.create(name=name, description="Test permission")
    assert perm.name == name
    assert perm.description == "Test permission"


@pytest.mark.asyncio
async def test_get_by_id(db_session):
    """Test getting a permission by ID."""
    repository = PermissionRepository(db_session)
    name = f"test_perm_{int(time.time() * 1000)}"
    created = await repository.create(name=name, description="Test permission")
    perm = await repository.get_by_id(created.id)
    assert perm is not None
    assert perm.name == name


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session):
    """Test getting a non-existent permission."""
    repository = PermissionRepository(db_session)
    perm = await repository.get_by_id(99999)
    assert perm is None


@pytest.mark.asyncio
async def test_get_by_name(db_session):
    """Test getting a permission by name."""
    repository = PermissionRepository(db_session)
    name = f"unique_perm_{int(time.time() * 1000)}"
    await repository.create(name=name, description="A unique permission")
    perm = await repository.get_by_name(name)
    assert perm is not None
    assert perm.name == name


@pytest.mark.asyncio
async def test_get_by_name_not_found(db_session):
    """Test getting a non-existent permission by name."""
    repository = PermissionRepository(db_session)
    perm = await repository.get_by_name("nonexistent")
    assert perm is None


@pytest.mark.asyncio
async def test_delete(db_session):
    """Test deleting a permission."""
    repository = PermissionRepository(db_session)
    name = f"to_delete_{int(time.time() * 1000)}"
    created = await repository.create(name=name, description="Will be deleted")
    result = await repository.delete(created.id)
    assert result is True
    perm = await repository.get_by_id(created.id)
    assert perm is None


@pytest.mark.asyncio
async def test_delete_not_found(db_session):
    """Test deleting a non-existent permission."""
    repository = PermissionRepository(db_session)
    result = await repository.delete(99999)
    assert result is False


@pytest.mark.asyncio
async def test_is_assigned_to_roles(db_session):
    """Test checking if a permission is assigned to any roles."""
    repository = PermissionRepository(db_session)
    name = f"assigned_perm_{int(time.time() * 1000)}"
    created = await repository.create(name=name, description="Test")

    # Initially not assigned
    is_assigned = await repository.is_assigned_to_roles(created.id)
    assert is_assigned is False

    # Create a role and assign permission
    role_repository = RoleRepository(db_session)
    role = await role_repository.create(name=f"test_role_{int(time.time() * 1000)}", description="Test role")
    await role_repository.add_permissions(role.id, [created.id])

    # Now should be assigned
    is_assigned = await repository.is_assigned_to_roles(created.id)
    assert is_assigned is True


@pytest.mark.asyncio
async def test_list_paginated_returns_assigned_roles_count(db_session):
    """Test that list_paginated returns assigned_roles_count correctly."""
    repository = PermissionRepository(db_session)
    role_repository = RoleRepository(db_session)

    # Create two test permissions
    perm1 = await repository.create(name=f"perm1_{int(time.time() * 1000)}", description="Perm 1")
    perm2 = await repository.create(name=f"perm2_{int(time.time() * 1000)}", description="Perm 2")

    # Initial state: all permissions have assigned_roles_count of 0
    permissions, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(perm1.id, 0) == 0
    assert counts.get(perm2.id, 0) == 0

    # Create a role and assign perm1 to it
    role = await role_repository.create(name=f"test_role_{int(time.time() * 1000)}", description="Test role")
    await role_repository.add_permissions(role.id, [perm1.id])

    # Verify perm1 has assigned_roles_count of 1, perm2 has 0
    permissions, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(perm1.id, 0) == 1
    assert counts.get(perm2.id, 0) == 0

    # Assign perm1 to another role
    role2 = await role_repository.create(name=f"test_role2_{int(time.time() * 1000)}", description="Test role 2")
    await role_repository.add_permissions(role2.id, [perm1.id])

    # Verify perm1 has assigned_roles_count of 2
    permissions, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(perm1.id, 0) == 2
    assert counts.get(perm2.id, 0) == 0

    # Clean up
    await role_repository.remove_permission(role.id, perm1.id)
    await role_repository.remove_permission(role2.id, perm1.id)
    await repository.delete(perm1.id)
    await repository.delete(perm2.id)
    await role_repository.delete(role.id)
    await role_repository.delete(role2.id)
