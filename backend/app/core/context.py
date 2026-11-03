"""请求上下文：request_id 与租户/用户上下文（contextvar 隔离并发）。"""
from __future__ import annotations

from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_tenant_id: ContextVar[int] = ContextVar("tenant_id", default=0)
_user_id: ContextVar[int] = ContextVar("user_id", default=0)


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


def set_tenant(tenant_id: int, user_id: int) -> None:
    _tenant_id.set(tenant_id)
    _user_id.set(user_id)


def get_tenant_id() -> int:
    return _tenant_id.get()


def get_user_id() -> int:
    return _user_id.get()
