from fastapi import APIRouter, Depends, Body, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, require_permissions
from app.schemas.common import ApiResponse
from app.handler.entity.request.permission import CreatePermissionRequest
from app.handler.entity.response.permission import PermissionResponse, PaginatedPermissionResponse
from app.service.permission_service import PermissionService
from app.repository.entity.user import User

router = APIRouter()


@router.post("/", response_model=ApiResponse[PermissionResponse], status_code=status.HTTP_201_CREATED)
async def create_permission(
    body: CreatePermissionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:write"])),
):
    service = PermissionService(db)
    try:
        perm = await service.create_permission(body.name, body.description)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ApiResponse(data=PermissionResponse(
        id=perm.id,
        name=perm.name,
        description=perm.description,
        created_at=perm.created_at,
        updated_at=perm.updated_at,
    ))


@router.get("/", response_model=ApiResponse[PaginatedPermissionResponse])
async def list_permissions(
    page: int = 1,
    page_size: int = 20,
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:read"])),
):
    service = PermissionService(db)
    entities, total, meta = await service.list_permissions(page, page_size, name)
    return ApiResponse(data=PaginatedPermissionResponse(
        items=[
            PermissionResponse(
                id=e.id,
                name=e.name,
                description=e.description,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in entities
        ],
        total=total,
        page=meta["page"],
        page_size=meta["page_size"],
        total_pages=meta["total_pages"],
    ))