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


@pytest.mark.asyncio
async def test_replace_permissions(db_session):
    """Test replacing all permissions for a role."""
    repository = RoleRepository(db_session)
    name = f"perm_role_{int(time.time() * 1000)}"
    role = await repository.create(name=name, description="Test")

    # Replace with permissions 1, 2
    result = await repository.replace_permissions(role.id, [1, 2])
    assert len(result) == 2

    # Replace with only permission 3
    result = await repository.replace_permissions(role.id, [3])
    assert len(result) == 1

    # Replace with empty list (clear all)
    result = await repository.replace_permissions(role.id, [])
    assert len(result) == 0


@pytest.mark.asyncio
async def test_update_with_permissions(db_session):
    """Test updating role name, description and permissions in one call."""
    repository = RoleRepository(db_session)
    name = f"update_perm_{int(time.time() * 1000)}"
    role = await repository.create(name=name, description="Original")

    # Update with permissions
    updated = await repository.update(role.id, description="New desc", permission_ids=[1, 2])
    assert updated is not None
    assert updated.description == "New desc"
    perms = await repository.get_role_permissions(role.id)
    assert len(perms) == 2


@pytest.mark.asyncio
async def test_update_clear_permissions_with_empty_list(db_session):
    """Test clearing all permissions by passing empty list."""
    repository = RoleRepository(db_session)
    name = f"clear_perm_{int(time.time() * 1000)}"
    role = await repository.create(name=name, description="Test")

    # Add permissions first
    await repository.replace_permissions(role.id, [1, 2, 3])
    perms = await repository.get_role_permissions(role.id)
    assert len(perms) == 3

    # Clear with empty list
    updated = await repository.update(role.id, permission_ids=[])
    assert updated is not None
    perms = await repository.get_role_permissions(role.id)
    assert len(perms) == 0


@pytest.mark.asyncio
async def test_update_without_changing_permissions(db_session):
    """Test that updating without permission_ids preserves existing permissions."""
    repository = RoleRepository(db_session)
    base_name = f"preserve_perm_{int(time.time() * 1000)}"
    role = await repository.create(name=base_name, description="Test")

    # Add permissions
    await repository.replace_permissions(role.id, [1, 2])
    perms_before = await repository.get_role_permissions(role.id)
    assert len(perms_before) == 2

    # Update only name, keep permissions - use unique name to avoid conflict
    unique_new_name = f"new_name_{int(time.time() * 1000)}"
    updated = await repository.update(role.id, name=unique_new_name)
    assert updated.name == unique_new_name
    perms_after = await repository.get_role_permissions(role.id)
    assert len(perms_after) == 2


@pytest.mark.asyncio
async def test_list_paginated_returns_assigned_users_count(db_session):
    """Test that list_paginated returns assigned_users_count correctly."""
    from app.repository.entity.user import User
    from app.tools.auth.hashing import get_password_hash

    repository = RoleRepository(db_session)

    # Create two test users
    user1 = User(
        username=f"user1_{int(time.time() * 1000)}",
        email=f"user1_{int(time.time() * 1000)}@test.com",
        password_hash=get_password_hash("password123"),
    )
    user2 = User(
        username=f"user2_{int(time.time() * 1000)}",
        email=f"user2_{int(time.time() * 1000)}@test.com",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Create two roles
    role1 = await repository.create(name=f"role1_{int(time.time() * 1000)}", description="Role 1")
    role2 = await repository.create(name=f"role2_{int(time.time() * 1000)}", description="Role 2")

    # Initially no users assigned - use large page_size to include all roles
    roles, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(role1.id, 0) == 0
    assert counts.get(role2.id, 0) == 0

    # Assign role1 to user1
    await repository.assign_role_to_user(user_id=user1.id, role_id=role1.id)

    # Use page_size large enough to include all roles (total roles is ~1300)
    roles, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(role1.id, 0) == 1
    assert counts.get(role2.id, 0) == 0

    # Assign role1 to user2 as well
    await repository.assign_role_to_user(user_id=user2.id, role_id=role1.id)

    # Use large enough page_size
    roles, total, counts = await repository.list_paginated(1, 99999)
    assert counts.get(role1.id, 0) == 2

    # Clean up
    await repository.remove_role_from_user(user_id=user1.id, role_id=role1.id)
    await repository.remove_role_from_user(user_id=user2.id, role_id=role1.id)
    await repository.delete(role1.id)
    await repository.delete(role2.id)
