import pytest
import time
from app.repository.role_repository import RoleRepository


@pytest.mark.asyncio
async def test_create_role(db_session):
    repository = RoleRepository(db_session)
    name = f"test_role_{int(time.time() * 1000)}"
    role = await repository.create(name=name, description="Test role")
    assert role.name == name
    assert role.description == "Test role"



@pytest.mark.asyncio
async def test_get_by_id(db_session):
    repository = RoleRepository(db_session)
    name = f"test_role_{int(time.time() * 1000)}"
    created = await repository.create(name=name, description="Test role")
    role = await repository.get_by_id(created.id)
    assert role is not None
    assert role.name == name


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session):
    repository = RoleRepository(db_session)
    role = await repository.get_by_id(99999)
    assert role is None


@pytest.mark.asyncio
async def test_get_by_name(db_session):
    repository = RoleRepository(db_session)
    name = f"unique_role_{int(time.time() * 1000)}"
    await repository.create(name=name, description="A unique role")
    role = await repository.get_by_name(name)
    assert role is not None
    assert role.name == name


@pytest.mark.asyncio
async def test_get_by_name_not_found(db_session):
    repository = RoleRepository(db_session)
    role = await repository.get_by_name("nonexistent")
    assert role is None


@pytest.mark.asyncio
async def test_list_all(db_session):
    repository = RoleRepository(db_session)
    name1 = f"role1_{int(time.time() * 1000)}"
    name2 = f"role2_{int(time.time() * 1000)}"
    await repository.create(name=name1, description="Role 1")
    await repository.create(name=name2, description="Role 2")
    roles = await repository.list_all()
    assert len(roles) >= 2
    names = [r.name for r in roles]
    assert name1 in names
    assert name2 in names


@pytest.mark.asyncio
async def test_update(db_session):
    repository = RoleRepository(db_session)
    name = f"to_update_{int(time.time() * 1000)}"
    created = await repository.create(name=name, description="Original desc")
    updated = await repository.update(created.id, description="New desc")
    assert updated is not None
    assert updated.description == "New desc"


@pytest.mark.asyncio
async def test_update_not_found(db_session):
    repository = RoleRepository(db_session)
    result = await repository.update(99999, name="should_fail")
    assert result is None


@pytest.mark.asyncio
async def test_delete(db_session):
    repository = RoleRepository(db_session)
    name = f"to_delete_{int(time.time() * 1000)}"
    created = await repository.create(name=name, description="Will be deleted")
    result = await repository.delete(created.id)
    assert result is True
    role = await repository.get_by_id(created.id)
    assert role is None


@pytest.mark.asyncio
async def test_delete_not_found(db_session):
    repository = RoleRepository(db_session)
    result = await repository.delete(99999)
    assert result is False
