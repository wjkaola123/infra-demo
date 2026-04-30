import time
import json
from typing import Callable
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings


MAX_LOG_LENGTH = 500


def truncate_json(data: str | None, max_length: int = MAX_LOG_LENGTH) -> str:
    """Truncate JSON string if too long."""
    if data is None:
        return "None"
    if len(data) > max_length:
        return f"{data[:max_length]}... (truncated)"
    return data


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request parameters and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        if not settings.DEBUG:
            return await call_next(request)

        start_time = time.time()

        request_body = None
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                try:
                    request_body = body.decode("utf-8")
                except Exception:
                    request_body = "<binary data>"
            request._body = body

        response = await call_next(request)

        process_time = time.time() - start_time

        response_body = ""
        try:
            if hasattr(response, "body"):
                response_body = response.body.decode("utf-8", errors="replace") if response.body else ""
            elif hasattr(response, "text"):
                response_body = response.text
            elif hasattr(response, "content"):
                response_body = response.content.decode("utf-8", errors="replace") if response.content else ""
        except Exception:
            response_body = "<unable to decode>"

        log_data = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s",
            "request_body": truncate_json(request_body) if request_body else None,
            "response_body": truncate_json(response_body),
        }

        print(json.dumps(log_data, indent=2, ensure_ascii=False))

        return response


def setup_logging_middleware(app: ASGIApp) -> None:
    """Add logging middleware to the application."""
    app.add_middleware(LoggingMiddleware)
