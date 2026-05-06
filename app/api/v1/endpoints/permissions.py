from fastapi import APIRouter, Depends, Body, status, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, require_permissions
from app.schemas.common import ApiResponse
from app.handler.entity.request.permission import CreatePermissionRequest, UpdatePermissionRequest
from app.handler.entity.response.permission import PermissionResponse, PaginatedPermissionResponse
from app.service.permission_service import PermissionService
from app.repository.entity.user import User

router = APIRouter()


@router.get("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:read"])),
):
    service = PermissionService(db)
    try:
        entity = await service.get_permission(permission_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return ApiResponse(data=PermissionResponse(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    ))


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


@router.put("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def update_permission(
    permission_id: int,
    body: UpdatePermissionRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:write"])),
):
    service = PermissionService(db)
    try:
        entity = await service.update_permission(permission_id, body.name, body.description)
    except ValueError as e:
        detail = str(e).lower()
        if "not found" in detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ApiResponse(data=PermissionResponse(
        id=entity.id,
        name=entity.name,
        description=entity.description,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    ))


@router.delete("/{permission_id}", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
async def delete_permission(
    permission_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["permissions:delete"])),
):
    service = PermissionService(db)
    try:
        deleted = await service.delete_permission(permission_id)
    except ValueError as e:
        detail = str(e).lower()
        if "not found" in detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return ApiResponse(data={"deleted": deleted})


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