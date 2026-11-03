"""统一响应封装。"""
from __future__ import annotations

from typing import Any

from app.core.context import get_request_id


def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": "OK", "message": message, "data": data, "request_id": get_request_id()}
