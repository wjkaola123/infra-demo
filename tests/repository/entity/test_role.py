import pytest
from datetime import datetime
from app.repository.entity.role import Role


def test_role_creation():
    role = Role(
        id=1,
        name="admin",
        description="Administrator role",
    )
    assert role.name == "admin"
    assert role.description == "Administrator role"