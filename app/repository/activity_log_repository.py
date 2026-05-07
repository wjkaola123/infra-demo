from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from app.repository.entity.activity_log import ActivityLog


class ActivityLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        actor_user_id: int,
        actor_username: str,
        action: str,
        resource_type: str,
        resource_id: int,
        old_value: dict | None,
        new_value: dict | None,
        ip_address: str | None,
    ) -> ActivityLog:
        log = ActivityLog(
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        actor_user_id: int | None = None,
        resource_type: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[list[ActivityLog], int]:
        conditions = []
        if actor_user_id is not None:
            conditions.append(ActivityLog.actor_user_id == actor_user_id)
        if resource_type:
            conditions.append(ActivityLog.resource_type == resource_type)
        if action:
            conditions.append(ActivityLog.action == action)
        if start_date:
            conditions.append(ActivityLog.created_at >= start_date)
        if end_date:
            conditions.append(ActivityLog.created_at <= end_date)

        where_clause = and_(*conditions) if conditions else True

        count_result = await self.session.execute(
            select(func.count(ActivityLog.id)).where(where_clause)
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(ActivityLog)
            .where(where_clause)
            .order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all()), total