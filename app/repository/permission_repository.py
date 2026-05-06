from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
