from datetime import datetime
from pydantic import BaseModel
from app.handler.entity.response.role import RoleResponse


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    roles: list[RoleResponse] = []

    model_config = {"from_attributes": True}


class PaginatedUserResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
