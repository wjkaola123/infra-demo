from app.repository.permission_repository import PermissionRepository
from app.repository.entity.role import Permission
from app.entity.permission import PermissionEntity
from sqlalchemy.ext.asyncio import AsyncSession


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repo = PermissionRepository(db)

    async def create_permission(self, name: str, description: str | None) -> PermissionEntity:
        existing = await self.repo.get_by_name(name)
        if existing:
            raise ValueError("Permission already exists")
        perm = await self.repo.create(name, description)
        return PermissionEntity(
            id=perm.id,
            name=perm.name,
            description=perm.description,
            created_at=perm.created_at,
            updated_at=perm.updated_at,
        )

    async def get_permission(self, permission_id: int) -> PermissionEntity:
        perm = await self.repo.get_by_id(permission_id)
        if not perm:
            raise ValueError("Permission not found")
        return PermissionEntity(
            id=perm.id,
            name=perm.name,
            description=perm.description,
            created_at=perm.created_at,
            updated_at=perm.updated_at,
        )

    async def list_permissions(self, page: int, page_size: int, name: str | None) -> tuple[list[PermissionEntity], int, dict]:
        items, total = await self.repo.list_paginated(page, page_size, name)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        entities = [
            PermissionEntity(
                id=p.id,
                name=p.name,
                description=p.description,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in items
        ]
        return entities, total, {"page": page, "page_size": page_size, "total_pages": total_pages}