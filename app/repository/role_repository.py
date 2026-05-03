from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repository.entity.role import Role, user_roles, role_permissions, Permission


class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: str | None = None) -> Role:
        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def get_by_id(self, role_id: int) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self.session.execute(select(Role))
        return list(result.scalars().all())

    async def list_paginated(self, page: int, page_size: int) -> tuple[list[Role], int]:
        offset = (page - 1) * page_size
        count_result = await self.session.execute(select(func.count(Role.id)))
        total = count_result.scalar() or 0
        result = await self.session.execute(
            select(Role).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def update(self, role: Role) -> Role:
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role: Role) -> None:
        await self.session.delete(role)
        await self.session.commit()

    async def add_permissions(self, role_id: int, permission_ids: list[int]) -> list[Permission]:
        role = await self.get_by_id(role_id)
        if not role:
            return []
        for perm_id in permission_ids:
            result = await self.session.execute(
                select(Permission).where(Permission.id == perm_id)
            )
            permission = result.scalar_one_or_none()
            if permission:
                role.permissions.append(permission)
        await self.session.commit()
        return role.permissions

    async def remove_permission(self, role_id: int, permission_id: int) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False
        for perm in role.permissions:
            if perm.id == permission_id:
                role.permissions.remove(perm)
                await self.session.commit()
                return True
        return False

    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        role = await self.get_by_id(role_id)
        return role.permissions if role else []

    async def assign_role_to_user(self, user_id: int, role_id: int) -> None:
        from app.repository.entity.user import User
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return
        role = await self.get_by_id(role_id)
        if not role:
            return
        user.roles.append(role)
        await self.session.commit()

    async def get_user_roles(self, user_id: int) -> list[Role]:
        from app.repository.entity.user import User
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return user.roles if user else []

    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        from app.repository.entity.user import User
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        role = await self.get_by_id(role_id)
        if not role:
            return False
        if role in user.roles:
            user.roles.remove(role)
            await self.session.commit()
            return True
        return False

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        from app.repository.entity.user import User
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return []
        permissions = []
        for role in user.roles:
            permissions.extend(role.permissions)
        return list(set(permissions))