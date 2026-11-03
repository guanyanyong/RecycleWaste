"""应用入口：配置校验 → 中间件 → 路由 → 健康检查 → 优雅停机。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import check_database, engine
from app.core.errors import register_exception_handlers
from app.core.logging import RequestContextMiddleware, setup_logging

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_database()  # 快速失败：数据库不可用直接启动失败
    logger.info(
        "application started",
        extra={"extra_data": {"env": settings.app_env, "db": settings.db_name}},
    )
    yield
    engine.dispose()
    logger.info("application stopped")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="再生资源回收过磅与结算系统 API",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/ready", tags=["系统"])
def ready():
    try:
        check_database()
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=503, content={"status": "unavailable", "db": "down"})
    return {"status": "ready", "db": "up"}
