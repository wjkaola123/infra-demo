from fastapi import APIRouter, Depends, Body, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, require_permissions
from app.schemas.common import ApiResponse
from app.handler.entity.request.permission import CreatePermissionRequest
from app.handler.entity.response.permission import PermissionResponse
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
    return ApiResponse(data=PermissionResponse.model_validate(perm, from_attributes=True))
