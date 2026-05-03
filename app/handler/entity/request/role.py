from pydantic import BaseModel, Field
from typing import Optional


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=255, description="Role description")


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Role name")
    description: Optional[str] = Field(None, max_length=255, description="Role description")


class PermissionAssignRequest(BaseModel):
    permission_ids: list[int] = Field(..., description="List of permission IDs")


class UserRoleAssignRequest(BaseModel):
    role_id: int = Field(..., description="Role ID")