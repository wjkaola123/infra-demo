from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repository.entity.user import User
from app.repository.entity.role import Role, Permission, user_roles, role_permissions


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign_role(self, user_id: int, role_name: str) -> bool:
        """Assign a role to a user."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        result = await self.db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        # Check if already has this role
        check = await self.db.execute(
            select(user_roles).where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id
            )
        )
        if check.scalar_one_or_none():
            return True  # Already has the role

        # Assign role
        await self.db.execute(
            user_roles.insert().values(user_id=user_id, role_id=role.id)
        )
        await self.db.commit()
        return True

    async def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if a user has a specific permission."""
        # Check if user is admin (has all permissions)
        admin_query = (
            select(Role.id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .where(Role.name == "admin")
        )
        admin_result = await self.db.execute(admin_query)
        if admin_result.scalar_one_or_none():
            return True

        # Check specific permission
        query = (
            select(Permission.name)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .where(Permission.name == permission)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_user_permissions(self, user_id: int) -> list[str]:
        """Get all permissions for a user."""
        # Check if user is admin
        admin_query = (
            select(Role.id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .where(Role.name == "admin")
        )
        admin_result = await self.db.execute(admin_query)
        if admin_result.scalar_one_or_none():
            # Return all permissions for admin
            all_perms = await self.db.execute(select(Permission.name))
            return [row[0] for row in all_perms.fetchall()]

        query = (
            select(Permission.name)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]

    async def get_user_roles(self, user_id: int) -> list[str]:
        """Get all roles for a user."""
        query = (
            select(Role.name)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]