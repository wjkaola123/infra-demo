from datetime import datetime
from pydantic import BaseModel


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PaginatedRoleResponse(BaseModel):
    items: list[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserRoleResponse(BaseModel):
    user_id: int
    role_id: int
    role: RoleResponse

    model_config = {"from_attributes": True}