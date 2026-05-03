from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.repository.role_repository import RoleRepository
from app.repository.entity.role import Role, Permission


class RoleService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.repo = RoleRepository(db)
        self.redis = redis

    async def create_role(self, name: str, description: str | None = None) -> Role:
        return await self.repo.create(name, description)

    async def get_role(self, role_id: int) -> Role | None:
        return await self.repo.get_by_id(role_id)

    async def list_roles(self) -> list[Role]:
        return await self.repo.list_all()

    async def list_roles_paginated(self, page: int = 1, page_size: int = 10) -> tuple[list[Role], int]:
        return await self.repo.list_paginated(page, page_size)

    async def update_role(self, role_id: int, name: str | None = None, description: str | None = None) -> Role | None:
        role = await self.repo.get_by_id(role_id)
        if not role:
            return None
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        return await self.repo.update(role)

    async def delete_role(self, role_id: int) -> bool:
        role = await self.repo.get_by_id(role_id)
        if not role:
            return False
        await self.repo.delete(role)
        return True

    async def assign_permissions(self, role_id: int, permission_ids: list[int]) -> list[Permission]:
        return await self.repo.add_permissions(role_id, permission_ids)

    async def remove_permission(self, role_id: int, permission_id: int) -> bool:
        return await self.repo.remove_permission(role_id, permission_id)

    async def get_role_permissions(self, role_id: int) -> list[Permission]:
        return await self.repo.get_role_permissions(role_id)

    async def get_user_roles(self, user_id: int) -> list[Role]:
        return await self.repo.get_user_roles(user_id)

    async def assign_role_to_user(self, user_id: int, role_id: int) -> None:
        await self.repo.assign_role_to_user(user_id, role_id)

    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        return await self.repo.remove_role_from_user(user_id, role_id)

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        return await self.repo.get_user_permissions(user_id)