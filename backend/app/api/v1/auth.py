"""认证接口。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.response import ok
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_principal
from app.core.errors import AuthError
from app.core.principal import Principal
from app.core.security import decode_token
from app.schemas.dto import LoginRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()

REFRESH_COOKIE = "rw_refresh"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/api/v1/auth",
    )


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    result, refresh = auth_service.login(db, payload.username, payload.password)
    _set_refresh_cookie(response, refresh)
    return ok(result.model_dump())


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise AuthError("登录已过期，请重新登录", code="REFRESH_MISSING")
    payload = decode_token(token, "refresh")
    access, user = auth_service.refresh_principal(db, int(payload["sub"]), int(payload["tid"]))
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    _set_refresh_cookie(response, token)
    return ok({"access_token": access, "token_type": "bearer", "user": user.model_dump()})


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return ok({"logged_out": True})


@router.get("/me")
def me(principal: Principal = Depends(get_principal)):
    return ok(auth_service.me(principal).model_dump())
