from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.dependencies import get_db, get_redis, get_current_user, require_permissions
from app.service.role_service import RoleService
from app.handler.entity.request.role import (
    RoleCreateRequest,
    RoleUpdateRequest,
    PermissionAssignRequest,
    UserRoleAssignRequest,
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
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:read")),
):
    service = RoleService(db, redis)
    roles, total = await service.list_roles_paginated(page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=PaginatedRoleResponse(
            items=[RoleResponse.model_validate(r) for r in roles],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.post("/", response_model=ApiResponse[RoleResponse], status_code=201)
async def create_role(
    role_data: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:write")),
):
    service = RoleService(db, redis)
    role = await service.create_role(role_data.name, role_data.description)
    return ApiResponse(data=RoleResponse.model_validate(role))


@router.get("/{role_id}", response_model=ApiResponse[RoleResponse])
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:read")),
):
    service = RoleService(db, redis)
    role = await service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return ApiResponse(data=RoleResponse.model_validate(role))


@router.put("/{role_id}", response_model=ApiResponse[RoleResponse])
async def update_role(
    role_id: int,
    role_data: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:write")),
):
    service = RoleService(db, redis)
    role = await service.update_role(role_id, role_data.name, role_data.description)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return ApiResponse(data=RoleResponse.model_validate(role))


@router.delete("/{role_id}", response_model=ApiResponse[dict])
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:delete")),
):
    service = RoleService(db, redis)
    deleted = await service.delete_role(role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
    return ApiResponse(message="success", data={"id": role_id})


@router.post("/{role_id}/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def assign_permissions(
    role_id: int,
    request: PermissionAssignRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:write")),
):
    service = RoleService(db, redis)
    permissions = await service.assign_permissions(role_id, request.permission_ids)
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])


@router.delete("/{role_id}/permissions/{permission_id}", response_model=ApiResponse[dict])
async def remove_permission(
    role_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:write")),
):
    service = RoleService(db, redis)
    removed = await service.remove_permission(role_id, permission_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Permission not found")
    return ApiResponse(message="success")


@router.get("/users/{user_id}/roles", response_model=ApiResponse[list[RoleResponse]])
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:read")),
):
    service = RoleService(db, redis)
    roles = await service.get_user_roles(user_id)
    return ApiResponse(data=[RoleResponse.model_validate(r) for r in roles])


@router.post("/users/{user_id}/roles", response_model=ApiResponse[UserRoleResponse])
async def assign_role_to_user(
    user_id: int,
    request: UserRoleAssignRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:write")),
):
    service = RoleService(db, redis)
    await service.assign_role_to_user(user_id, request.role_id)
    role = await service.get_role(request.role_id)
    return ApiResponse(
        data=UserRoleResponse(user_id=user_id, role_id=request.role_id, role=RoleResponse.model_validate(role))
    )


@router.delete("/users/{user_id}/roles/{role_id}", response_model=ApiResponse[dict])
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:write")),
):
    service = RoleService(db, redis)
    removed = await service.remove_role_from_user(user_id, role_id)
    if not removed:
        raise HTTPException(status_code=404, detail="User role not found")
    return ApiResponse(message="success")


@router.get("/users/{user_id}/permissions", response_model=ApiResponse[list[PermissionResponse]])
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(require_permissions("roles:read")),
):
    service = RoleService(db, redis)
    permissions = await service.get_user_permissions(user_id)
    return ApiResponse(data=[PermissionResponse.model_validate(p) for p in permissions])