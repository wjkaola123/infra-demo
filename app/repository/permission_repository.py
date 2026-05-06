from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repository.entity.role import Permission


class PermissionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: str | None) -> Permission:
        perm = Permission(name=name, description=description)
        self.session.add(perm)
        await self.session.commit()
        await self.session.refresh(perm)
        return perm

    async def get_by_name(self, name: str) -> Permission | None:
        result = await self.session.execute(select(Permission).where(Permission.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, permission_id: int) -> Permission | None:
        result = await self.session.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(self, page: int, page_size: int, name: str | None = None) -> tuple[list[Permission], int]:
        offset = (page - 1) * page_size
        base_query = select(Permission)
        count_query = select(func.count(Permission.id))

        if name:
            name_filter = Permission.name.ilike(f"%{name}%")
            base_query = base_query.where(name_filter)
            count_query = count_query.where(name_filter)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        result = await self.session.execute(
            base_query.offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total
