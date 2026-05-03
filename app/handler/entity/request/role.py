from pydantic import BaseModel


class RoleCreateRequest(BaseModel):
    name: str
    description: str | None = None


class RoleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class PermissionAssignRequest(BaseModel):
    permission_ids: list[int]


class UserRoleAssignRequest(BaseModel):
    role_id: int