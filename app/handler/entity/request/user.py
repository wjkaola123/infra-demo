from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
