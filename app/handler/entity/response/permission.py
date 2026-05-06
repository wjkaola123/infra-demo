from pydantic import BaseModel
from datetime import datetime


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime | None
