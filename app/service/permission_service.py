from app.repository.permission_repository import PermissionRepository
from app.repository.entity.role import Permission
from sqlalchemy.ext.asyncio import AsyncSession


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repo = PermissionRepository(db)

    async def create_permission(self, name: str, description: str | None) -> Permission:
        existing = await self.repo.get_by_name(name)
        if existing:
            raise ValueError("Permission already exists")
        return await self.repo.create(name, description)
