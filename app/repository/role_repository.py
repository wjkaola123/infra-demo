from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repository.entity.role import Role


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
        result = await self.session.execute(select(Role).where(Role.id == role_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self.session.execute(select(Role))
        return list(result.scalars().all())

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