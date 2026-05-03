from pydantic import BaseModel, Field
from typing import Optional


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=255, description="角色描述")



class RoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=255, description="角色描述")


class PermissionAssignRequest(BaseModel):
    permission_ids: list[int] = Field(..., description="权限ID列表")


class UserRoleAssignRequest(BaseModel):
    role_id: int = Field(..., description="角色ID")