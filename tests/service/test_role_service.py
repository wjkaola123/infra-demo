import pytest
import time
from app.service.role_service import RoleService
from app.repository.role_repository import RoleRepository


@pytest.mark.asyncio
async def test_role_service_create(db_session):
    """Test RoleService.create_role."""
    service = RoleService(db_session, redis=None)
    name = f"test_svc_{int(time.time() * 1000)}"
    role = await service.create_role(name, "Test description")
    assert role.name == name
    assert role.description == "Test description"


@pytest.mark.asyncio
async def test_role_service_get(db_session):
    """Test RoleService.get_role."""
    service = RoleService(db_session, redis=None)
    name = f"get_test_{int(time.time() * 1000)}"
    created = await service.create_role(name, "Test")
    role = await service.get_role(created.id)
    assert role is not None
    assert role.name == name


@pytest.mark.asyncio
async def test_role_service_list(db_session):
    """Test RoleService.list_roles."""
    service = RoleService(db_session, redis=None)
    name = f"list_test_{int(time.time() * 1000)}"
    await service.create_role(name, "Test")
    roles = await service.list_roles()
    assert len(roles) >= 1
    names = [r.name for r in roles]
    assert name in names


@pytest.mark.asyncio
async def test_role_service_update(db_session):
    """Test RoleService.update_role."""
    service = RoleService(db_session, redis=None)
    name = f"update_test_{int(time.time() * 1000)}"
    created = await service.create_role(name, "Original")
    updated = await service.update_role(created.id, description="Updated")
    assert updated is not None
    assert updated.description == "Updated"


@pytest.mark.asyncio
async def test_role_service_delete(db_session):
    """Test RoleService.delete_role."""
    service = RoleService(db_session, redis=None)
    name = f"delete_test_{int(time.time() * 1000)}"
    created = await service.create_role(name, "To delete")
    result = await service.delete_role(created.id)
    assert result is True
    role = await service.get_role(created.id)
    assert role is None


@pytest.mark.asyncio
async def test_role_service_delete_nonexistent(db_session):
    """Test RoleService.delete_role with non-existent ID."""
    service = RoleService(db_session, redis=None)
    result = await service.delete_role(99999)
    assert result is False


@pytest.mark.asyncio
async def test_role_service_get_user_roles(db_session):
    """Test RoleService.get_user_roles."""
    service = RoleService(db_session, redis=None)
    # This just verifies the method doesn't crash - user may not exist
    roles = await service.get_user_roles(99999)
    assert isinstance(roles, list)



@pytest.mark.asyncio
async def test_role_service_get_user_permissions(db_session):
    """Test RoleService.get_user_permissions."""
    service = RoleService(db_session, redis=None)
    permissions = await service.get_user_permissions(99999)
    assert isinstance(permissions, list)


@pytest.mark.asyncio
async def test_role_service_replace_permissions(db_session):
    """Test RoleService.replace_permissions."""
    service = RoleService(db_session, redis=None)
    name = f"replace_perm_{int(time.time() * 1000)}"
    role = await service.create_role(name, "Test")

    # Replace with permissions
    result = await service.replace_permissions(role.id, [1, 2])
    assert len(result) == 2

    # Clear permissions
    result = await service.replace_permissions(role.id, [])
    assert len(result) == 0
