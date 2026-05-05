from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role_ids: list[int] | None = None


class UserUpdateRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
    role_ids: list[int] | None = None


class UserListRequest(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
