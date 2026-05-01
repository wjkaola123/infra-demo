from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr


class UserUpdateRequest(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
