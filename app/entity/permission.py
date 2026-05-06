from dataclasses import dataclass
from datetime import datetime


@dataclass
class PermissionEntity:
    id: int
    name: str
    description: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
