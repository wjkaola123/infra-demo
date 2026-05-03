import pytest
from app.repository.role_repository import RoleRepository


@pytest.mark.asyncio
async def test_create_role(db_session):
    repository = RoleRepository(db_session)
    role = await repository.create(name="admin", description="Admin role")
    assert role.name == "admin"
    assert role.description == "Admin role"


@pytest.mark.asyncio
async def test_get_by_id(db_session):
    repository = RoleRepository(db_session)
    # Create a role first
    created = await repository.create(name="test_role", description="Test role")
    # Retrieve it
    role = await repository.get_by_id(created.id)
    assert role is not None
    assert role.name == "test_role"


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session):
    repository = RoleRepository(db_session)
    role = await repository.get_by_id(99999)
    assert role is None


@pytest.mark.asyncio
async def test_get_by_name(db_session):
    repository = RoleRepository(db_session)
    await repository.create(name="unique_role", description="A unique role")
    role = await repository.get_by_name("unique_role")
    assert role is not None
    assert role.name == "unique_role"


@pytest.mark.asyncio
async def test_get_by_name_not_found(db_session):
    repository = RoleRepository(db_session)
    role = await repository.get_by_name("nonexistent")
    assert role is None


@pytest.mark.asyncio
async def test_list_all(db_session):
    repository = RoleRepository(db_session)
    await repository.create(name="role1", description="Role 1")
    await repository.create(name="role2", description="Role 2")
    roles = await repository.list_all()
    assert len(roles) >= 2
    names = [r.name for r in roles]
    assert "role1" in names
    assert "role2" in names


@pytest.mark.asyncio
async def test_update(db_session):
    repository = RoleRepository(db_session)
    created = await repository.create(name="to_update", description="Original desc")
    updated = await repository.update(created.id, name="updated_name", description="New desc")
    assert updated is not None
    assert updated.name == "updated_name"
    assert updated.description == "New desc"


@pytest.mark.asyncio
async def test_update_not_found(db_session):
    repository = RoleRepository(db_session)
    result = await repository.update(99999, name="should_fail")
    assert result is None


@pytest.mark.asyncio
async def test_delete(db_session):
    repository = RoleRepository(db_session)
    created = await repository.create(name="to_delete", description="Will be deleted")
    result = await repository.delete(created.id)
    assert result is True
    # Verify it's gone
    role = await repository.get_by_id(created.id)
    assert role is None


@pytest.mark.asyncio
async def test_delete_not_found(db_session):
    repository = RoleRepository(db_session)
    result = await repository.delete(99999)
    assert result is False