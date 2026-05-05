from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserEntity:
    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
