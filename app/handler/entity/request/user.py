from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr


class UserUpdateRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class UserListRequest(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
