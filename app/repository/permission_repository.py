from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repository.entity.role import Permission, role_permissions


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

    async def list_paginated(self, page: int, page_size: int, name: str | None = None) -> tuple[list[Permission], int, dict[int, int]]:
        offset = (page - 1) * page_size

        # 计数子查询：统计每个 permission 关联的 role 数量
        role_count_subquery = (
            select(
                role_permissions.c.permission_id,
                func.count(role_permissions.c.role_id).label('role_count')
            )
            .group_by(role_permissions.c.permission_id)
            .subquery()
        )

        # 基础查询：left outer join 计数子查询
        base_query = (
            select(Permission, func.coalesce(role_count_subquery.c.role_count, 0).label('assigned_roles_count'))
            .outerjoin(role_count_subquery, Permission.id == role_count_subquery.c.permission_id)
        )

        # 名称过滤
        if name:
            name_filter = Permission.name.ilike(f"%{name}%")
            base_query = base_query.where(name_filter)

        # 总数查询（不受分页影响）
        count_query = select(func.count(Permission.id))
        if name:
            count_query = count_query.where(name_filter)

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # 分页查询
        result = await self.session.execute(
            base_query.order_by(Permission.id).offset(offset).limit(page_size)
        )

        # 组装返回结果
        permissions = []
        counts = {}
        for row in result.all():
            perm = row[0]
            count = row[1]
            permissions.append(perm)
            counts[perm.id] = count

        return permissions, total, counts

    async def update(self, permission_id: int, name: str | None = None, description: str | None = None) -> Permission | None:
        perm = await self.get_by_id(permission_id)
        if not perm:
            return None
        if name is not None:
            perm.name = name
        if description is not None:
            perm.description = description
        await self.session.commit()
        await self.session.refresh(perm)
        return perm

    async def is_assigned_to_roles(self, permission_id: int) -> bool:
        result = await self.session.execute(
            select(role_permissions).where(
                role_permissions.c.permission_id == permission_id
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, permission_id: int) -> bool:
        permission = await self.get_by_id(permission_id)
        if not permission:
            return False
        await self.session.delete(permission)
        await self.session.commit()
        return True
