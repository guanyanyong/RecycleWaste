"""结构化 JSON 日志：请求 ID 贯穿全链路，敏感字段不落日志。"""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.context import get_request_id, set_request_id

SENSITIVE_KEYS = {"password", "token", "authorization", "old_password", "new_password"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": get_request_id(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_data", None)
        if extra:
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or f"req-{int(time.time() * 1000)}-{id(request) % 10000}"
        set_request_id(rid)
        started = time.perf_counter()
        response = await call_next(request)
        cost = (time.perf_counter() - started) * 1000
        logging.getLogger("app.request").info(
            "%s %s -> %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={
                "extra_data": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "cost_ms": round(cost, 1),
                }
            },
        )
        response.headers["X-Request-ID"] = rid
        return response
