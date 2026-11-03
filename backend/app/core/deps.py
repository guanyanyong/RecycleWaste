"""FastAPI 依赖：当前登录主体、权限校验。"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.context import set_tenant
from app.core.errors import AuthError, PermissionError_
from app.core.principal import Principal
from app.core.security import decode_token
from app.repositories.user_repo import load_principal
from app.core.database import get_db

bearer = HTTPBearer(auto_error=False)


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Principal:
    if not credentials:
        raise AuthError("请先登录")
    payload = decode_token(credentials.credentials, "access")
    user_id = int(payload.get("sub", 0))
    tenant_id = int(payload.get("tid", 0))
    principal = load_principal(db, user_id, tenant_id)
    if not principal:
        raise AuthError("账号或租户已被停用")
    set_tenant(tenant_id, user_id)
    return principal


def require_perm(perm: str) -> Callable[[Principal], Principal]:
    def _checker(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_perm(perm):
            raise PermissionError_(f"缺少权限：{perm}")
        return principal

    return _checker
