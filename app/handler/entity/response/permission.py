from pydantic import BaseModel
from datetime import datetime


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
    assigned_roles_count: int = 0


class PaginatedPermissionResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
