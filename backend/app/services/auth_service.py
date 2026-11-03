"""认证业务：登录、刷新、主体信息。"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthError
from app.core.principal import Principal
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.repositories import user_repo
from app.repositories.user_repo import load_principal
from app.schemas.dto import LoginResponse, UserInfo

settings = get_settings()


def _to_info(p: Principal) -> UserInfo:
    return UserInfo(
        user_id=p.user_id,
        username=p.username,
        real_name=p.real_name,
        tenant_id=p.tenant_id,
        tenant_name=p.tenant_name,
        roles=p.roles,
        permissions=sorted(p.permissions) if not p.is_tenant_admin else ["*"],
    )


def login(db: Session, username: str, password: str) -> tuple[LoginResponse, str]:
    user = user_repo.find_user_by_username(db, username)
    if not user or user.status != 1 or not verify_password(password, user.password):
        raise AuthError("用户名或密码错误", code="LOGIN_FAILED")
    ut = user_repo.first_tenant_of_user(db, user.user_id)
    if not ut:
        raise AuthError("该账号未绑定任何租户", code="NO_TENANT")
    principal = load_principal(db, user.user_id, ut.tenant_id)
    if not principal:
        raise AuthError("账号或租户已被停用", code="ACCOUNT_DISABLED")

    access = create_access_token(user.user_id, ut.tenant_id)
    refresh = create_refresh_token(user.user_id, ut.tenant_id)
    resp = LoginResponse(
        access_token=access,
        expires_in=settings.access_token_minutes * 60,
        user=_to_info(principal),
    )
    return resp, refresh


def refresh_principal(db: Session, user_id: int, tenant_id: int) -> tuple[str, UserInfo]:
    principal = load_principal(db, user_id, tenant_id)
    if not principal:
        raise AuthError("登录状态已失效，请重新登录", code="REFRESH_FAILED")
    return create_access_token(user_id, tenant_id), _to_info(principal)


def me(principal: Principal) -> UserInfo:
    return _to_info(principal)
