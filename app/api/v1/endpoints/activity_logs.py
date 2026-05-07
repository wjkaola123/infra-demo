from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.dependencies import get_db, get_current_user
from app.repository.entity.user import User
from app.repository.activity_log_repository import ActivityLogRepository
from app.handler.entity.response.activity_log import ActivityLogResponse, PaginatedActivityLogResponse
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[PaginatedActivityLogResponse])
async def list_activity_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=10000, description="Items per page"),
    actor_user_id: int | None = Query(None, description="Filter by actor user ID"),
    resource_type: str | None = Query(None, description="Filter by resource type: user, role, permission"),
    action: str | None = Query(None, description="Filter by action: CREATE, UPDATE, DELETE"),
    start_date: datetime | None = Query(None, description="Filter from date"),
    end_date: datetime | None = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = ActivityLogRepository(db)
    logs, total = await repo.list_paginated(
        page=page,
        page_size=page_size,
        actor_user_id=actor_user_id,
        resource_type=resource_type,
        action=action,
        start_date=start_date,
        end_date=end_date,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=PaginatedActivityLogResponse(
            items=[ActivityLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )
