"""类型化业务错误与全局异常处理。"""
from __future__ import annotations

from typing import Any

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger("app.error")


class AppError(Exception):
    """业务异常基类：客户端只会看到规范化结构，不暴露内部细节。"""

    def __init__(
        self,
        message: str,
        *,
        code: str = "BIZ_ERROR",
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "NOT_FOUND") -> None:
        super().__init__(message, code=code, status_code=404)


class AuthError(AppError):
    def __init__(self, message: str = "登录状态无效或已过期", code: str = "UNAUTHORIZED") -> None:
        super().__init__(message, code=code, status_code=401)


class PermissionError_(AppError):
    def __init__(self, message: str = "没有操作权限", code: str = "FORBIDDEN") -> None:
        super().__init__(message, code=code, status_code=403)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "CONFLICT") -> None:
        super().__init__(message, code=code, status_code=409)


def _envelope(code: str, message: str, request_id: str, details: Any = None) -> dict:
    return {"code": code, "message": message, "data": details, "request_id": request_id}


def register_exception_handlers(app: FastAPI) -> None:
    from app.core.context import get_request_id

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, get_request_id(), exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_envelope("VALIDATION_ERROR", "请求参数校验失败", get_request_id(), exc.errors()),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("integrity error: %s", exc.orig)
        text = str(exc.orig)
        if "uk_" in text or "Duplicate" in text:
            message = "数据重复，请检查唯一性字段（单号/编码）"
        elif "foreign key" in text.lower():
            message = "存在关联数据，操作被拒绝"
        else:
            message = "数据约束校验失败"
        return JSONResponse(
            status_code=409, content=_envelope("DB_CONSTRAINT", message, get_request_id())
        )

    @app.exception_handler(SQLAlchemyError)
    async def _db_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("database error: %s", exc)
        return JSONResponse(
            status_code=500, content=_envelope("DB_ERROR", "数据库操作失败", get_request_id())
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc)
        return JSONResponse(
            status_code=500, content=_envelope("INTERNAL_ERROR", "服务器内部错误", get_request_id())
        )
