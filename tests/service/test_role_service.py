import pytest
from app.service.role_service import RoleService
from app.repository.role_repository import RoleRepository


@pytest.mark.asyncio
async def test_role_service_create(db_session):
    """Test RoleService.create_role."""
    service = RoleService(db_session, redis=None)
    role = await service.create_role("test_service_role", "Test description")
    assert role.name == "test_service_role"
    assert role.description == "Test description"


@pytest.mark.asyncio
async def test_role_service_get(db_session):
    """Test RoleService.get_role."""
    service = RoleService(db_session, redis=None)
    # Create a role first
    created = await service.create_role("get_test_svc", "Test")
    # Get the role
    role = await service.get_role(created.id)
    assert role is not None
    assert role.name == "get_test_svc"


@pytest.mark.asyncio
async def test_role_service_list(db_session):
    """Test RoleService.list_roles."""
    service = RoleService(db_session, redis=None)
    # Create some roles
    await service.create_role("list_svc_1", "Test 1")
    await service.create_role("list_svc_2", "Test 2")
    # List roles
    roles = await service.list_roles()
    assert len(roles) >= 2


@pytest.mark.asyncio
async def test_role_service_update(db_session):
    """Test RoleService.update_role."""
    service = RoleService(db_session, redis=None)
    # Create a role
    created = await service.create_role("update_svc_test", "Original")
    # Update it
    updated = await service.update_role(created.id, name="updated_svc_name", description="New desc")
    assert updated is not None
    assert updated.name == "updated_svc_name"
    assert updated.description == "New desc"


@pytest.mark.asyncio
async def test_role_service_delete(db_session):
    """Test RoleService.delete_role."""
    service = RoleService(db_session, redis=None)
    # Create a role
    created = await service.create_role("delete_svc_test", "To delete")
    # Delete it
    result = await service.delete_role(created.id)
    assert result is True
    # Verify it's gone
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
    roles = await service.get_user_roles(1)
    assert isinstance(roles, list)


@pytest.mark.asyncio
async def test_role_service_get_user_permissions(db_session):
    """Test RoleService.get_user_permissions."""
    service = RoleService(db_session, redis=None)
    permissions = await service.get_user_permissions(1)
    assert isinstance(permissions, list)