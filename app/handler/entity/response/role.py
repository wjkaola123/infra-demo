from pydantic import BaseModel
from datetime import datetime
from typing import Optional



class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    permissions: list["PermissionResponse"] = []

    model_config = {"from_attributes": True}


class PaginatedRoleResponse(BaseModel):
    items: list[RoleResponse]
    total: int
    page: int
    page_size: int


class UserRoleResponse(BaseModel):
    user_id: int
    role_id: int
    created_at: datetime

    model_config = {"from_attributes": True}