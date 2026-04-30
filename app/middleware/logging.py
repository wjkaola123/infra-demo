import time
import json
from starlette.types import ASGIApp, Receive, Send, Scope
from app.config import settings

MAX_LOG_LENGTH = 500


def truncate_json(data: str | None, max_length: int = MAX_LOG_LENGTH) -> str:
    """Truncate JSON string if too long."""
    if data is None:
        return "None"
    if len(data) > max_length:
        return f"{data[:max_length]}... (truncated)"
    return data


class LoggingMiddleware:
    """ASGI Middleware to log request parameters and responses."""

    def __init__(self, app: ASGIApp):
        self.app = app
        print(f"[LoggingMiddleware] Initialized, DEBUG={settings.DEBUG}")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        print(f"[LoggingMiddleware] Intercepted: type={scope['type']}")
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not settings.DEBUG:
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope.get("method", "")

        request_body = None
        if method in ("POST", "PUT", "PATCH"):
            body_event = await receive()
            body = body_event.get("body", b"")
            if body:
                try:
                    request_body = body.decode("utf-8")
                except Exception:
                    request_body = "<binary data>"
            scope["_orig_body"] = body
            receive = self._create_receive(body_event)

        response_body = bytearray()
        status_code = 0

        async def send_with_logging(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            elif message["type"] == "http.response.body":
                body_chunk = message.get("body", b"")
                if body_chunk:
                    response_body.extend(body_chunk)
            await send(message)

        await self.app(scope, receive, send_with_logging)

        process_time = time.time() - start_time

        try:
            response_str = response_body.decode("utf-8", errors="replace")
        except Exception:
            response_str = "<unable to decode>"

        log_data = {
            "method": method,
            "url": f"{scope.get('scheme', 'http')}://{scope.get('host', '')}{scope.get('path', '')}",
            "status_code": status_code,
            "process_time": f"{process_time:.3f}s",
            "request_body": truncate_json(request_body) if request_body else None,
            "response_body": truncate_json(response_str),
        }

        print(json.dumps(log_data, indent=2, ensure_ascii=False))

    def _create_receive(self, body_event: dict):
        async def receive():
            return body_event
        return receive


def setup_logging_middleware(app: ASGIApp) -> None:
    """Add logging middleware to the application."""
    app.add_middleware(LoggingMiddleware)
