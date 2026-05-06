from pydantic import BaseModel, Field, field_validator
import re


class CreatePermissionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+:[a-z0-9_]+$", v):
            raise ValueError("Format must be 'resource:action' with lowercase letters, numbers, underscores")
        return v


class UpdatePermissionRequest(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-z0-9_]+:[a-z0-9_]+$", v):
            raise ValueError("Format must be 'resource:action' with lowercase letters, numbers, underscores")
        return v
