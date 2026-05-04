from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
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
            select(Role).where(Role.id == role_id).options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self.session.execute(
            select(Role).options(selectinload(Role.permissions))
        )
        return list(result.scalars().all())

    async def list_paginated(self, page: int, page_size: int) -> tuple[list[Role], int]:
        offset = (page - 1) * page_size
        count_result = await self.session.execute(select(func.count(Role.id)))
        total = count_result.scalar() or 0
        result = await self.session.execute(
            select(Role).offset(offset).limit(page_size).options(selectinload(Role.permissions))
        )
        return list(result.scalars().all()), total

    async def update(self, role_id: int, name: str | None = None, description: str | None = None) -> Role | None:
        role = await self.get_by_id(role_id)
        if not role:
            return None
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role_id: int) -> bool:
        role = await self.get_by_id(role_id)
        if not role:
            return False
        await self.session.delete(role)
        await self.session.commit()
        return True

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
                await self.session.execute(
                    role_permissions.insert().values(role_id=role_id, permission_id=perm_id)
                )
        await self.session.commit()
        # Return permissions directly from query
        result = await self.session.execute(
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
        )
        return list(result.scalars().all())

    async def remove_permission(self, role_id: int, permission_id: int) -> bool:
        result = await self.session.execute(
            select(role_permissions)
            .where(role_permissions.c.role_id == role_id)
            .where(role_permissions.c.permission_id == permission_id)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            return False
        await self.session.execute(
            role_permissions.delete()
            .where(role_permissions.c.role_id == role_id)
            .where(role_permissions.c.permission_id == permission_id)
        )
        await self.session.commit()
        return True

    async def replace_permissions(self, role_id: int, permission_ids: list[int]) -> list[Permission]:
        role = await self.get_by_id(role_id)
        if not role:
            return []
        await self.session.execute(
            role_permissions.delete().where(role_permissions.c.role_id == role_id)
        )
        for perm_id in permission_ids:
            result = await self.session.execute(
                select(Permission).where(Permission.id == perm_id)
            )
            permission = result.scalar_one_or_none()
            if permission:
                await self.session.execute(
                    role_permissions.insert().values(role_id=role_id, permission_id=perm_id)
                )
        await self.session.commit()
        result = await self.session.execute(
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
        )
        return list(result.scalars().all())

    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        result = await self.session.execute(
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .where(role_permissions.c.role_id == role_id)
        )
        return list(result.scalars().all())


    async def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        from app.repository.entity.user import User
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        result = await self.session.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            return False
        check = await self.session.execute(
            select(user_roles)
            .where(user_roles.c.user_id == user_id)
            .where(user_roles.c.role_id == role_id)
        )
        if check.scalar_one_or_none():
            return True
        await self.session.execute(
            user_roles.insert().values(user_id=user_id, role_id=role_id)
        )
        await self.session.commit()
        return True

    async def get_user_roles(self, user_id: int) -> list[Role]:
        result = await self.session.execute(
            select(Role)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .options(selectinload(Role.permissions))
        )
        return list(result.scalars().all())

    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        result = await self.session.execute(
            select(user_roles)
            .where(user_roles.c.user_id == user_id)
            .where(user_roles.c.role_id == role_id)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            return False
        await self.session.execute(
            user_roles.delete()
            .where(user_roles.c.user_id == user_id)
            .where(user_roles.c.role_id == role_id)
        )
        await self.session.commit()
        return True

    async def list_all_permissions(self) -> list[Permission]:
        result = await self.session.execute(select(Permission))
        return list(result.scalars().all())

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        result = await self.session.execute(
            select(Permission)
            .join(role_permissions, role_permissions.c.permission_id == Permission.id)
            .join(Role, Role.id == role_permissions.c.role_id)
            .join(user_roles, user_roles.c.role_id == Role.id)
            .where(user_roles.c.user_id == user_id)
            .distinct()
        )
        return list(result.scalars().all())
