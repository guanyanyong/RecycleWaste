"""v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1 import auth, basic, dashboard, reports, settlements, weigh

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(weigh.router)
api_router.include_router(settlements.router)
api_router.include_router(basic.router)
api_router.include_router(reports.router)
