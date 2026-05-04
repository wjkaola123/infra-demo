from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis, get_current_user, require_permissions
from app.service.role_service import RoleService
from app.handler.entity.request.role import (
    RoleCreateRequest,
    RoleUpdateRequest,
    UserRoleAssignRequest,
    RolePermissionUpdateRequest,
)
from app.handler.entity.response.role import (
    RoleResponse,
    PermissionResponse,
    PaginatedRoleResponse,
    UserRoleResponse,
)
from app.repository.entity.user import User
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/", response_model=ApiResponse[PaginatedRoleResponse])
async def list_roles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    name: str | None = Query(None, description="Filter by role name (case-insensitive contains)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:read"])),
):
    service = RoleService(db, redis)
    roles, total, user_counts = await service.list_roles_paginated(page, page_size, name)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    items = []
    for r in roles:
        role_response = RoleResponse.model_validate(r)
        role_response.assigned_users_count = user_counts.get(r.id, 0)
        items.append(role_response)
    return ApiResponse(
        data=PaginatedRoleResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:read"])),
):
    service = RoleService(db, redis)
    permissions = await service.list_permissions()
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])


@router.get("/{role_id}", response_model=ApiResponse[RoleResponse])
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:read"])),
):
    service = RoleService(db, redis)
    role = await service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return ApiResponse(data=RoleResponse.model_validate(role))


@router.post("/", response_model=ApiResponse[RoleResponse], status_code=201)
async def create_role(
    request: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:write"])),
):
    service = RoleService(db, redis)
    role = await service.create_role(request.name, request.description, request.permission_ids)
    return ApiResponse(data=RoleResponse.model_validate(role))


@router.put("/{role_id}", response_model=ApiResponse[RoleResponse])
async def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:write"])),
):
    service = RoleService(db, redis)
    role = await service.update_role(role_id, request.name, request.description, request.permission_ids)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return ApiResponse(data=RoleResponse.model_validate(role))



@router.delete("/{role_id}", response_model=ApiResponse[dict])
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:delete"])),
):
    service = RoleService(db, redis)
    success = await service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return ApiResponse(data={"deleted": True})


@router.get("/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:read"])),
):
    service = RoleService(db, redis)
    permissions = await service.list_permissions()
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])


@router.put("/{role_id}/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def update_role_permissions(
    role_id: int,
    request: RolePermissionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:write"])),
):
    service = RoleService(db, redis)
    permissions = await service.replace_permissions(role_id, request.permission_ids)
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])


@router.get("/users/{user_id}/roles", response_model=ApiResponse[list[RoleResponse]])
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:read"])),
):
    service = RoleService(db, redis)
    roles = await service.get_user_roles(user_id)
    return ApiResponse(data=[RoleResponse.model_validate(r) for r in roles])


@router.post("/users/{user_id}/roles", response_model=ApiResponse[dict])
async def assign_role_to_user(
    user_id: int,
    request: UserRoleAssignRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:write"])),
):
    service = RoleService(db, redis)
    success = await service.assign_role_to_user(user_id, request.role_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or role not found")
    return ApiResponse(data={"assigned": True})


@router.delete("/users/{user_id}/roles/{role_id}", response_model=ApiResponse[dict])
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:write"])),
):
    service = RoleService(db, redis)
    success = await service.remove_role_from_user(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return ApiResponse(data={"removed": True})


@router.get("/users/{user_id}/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis | None = Depends(get_redis),
    current_user: User = Depends(require_permissions(["roles:read"])),
):
    service = RoleService(db, redis)
    permissions = await service.get_user_permissions(user_id)
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])