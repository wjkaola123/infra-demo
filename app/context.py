from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class AuditContext:
    user_id: int
    username: str
    ip_address: str | None = None

audit_context: ContextVar[AuditContext | None] = ContextVar("audit_context", default=None)

