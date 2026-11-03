"""用户 / 角色 / 权限数据访问。"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.principal import Principal
from app.models.entities import (
    Permission,
    Role,
    RolePermission,
    Tenant,
    User,
    UserTenant,
    UserTenantRole,
)


def find_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_tenant(db: Session, tenant_id: int) -> Tenant | None:
    return db.get(Tenant, tenant_id)


def get_user_tenant(db: Session, user_id: int, tenant_id: int) -> UserTenant | None:
    return db.get(UserTenant, (user_id, tenant_id))


def first_tenant_of_user(db: Session, user_id: int) -> UserTenant | None:
    return db.scalar(select(UserTenant).where(UserTenant.user_id == user_id, UserTenant.status == 1))


def load_principal(db: Session, user_id: int, tenant_id: int) -> Principal | None:
    user = db.get(User, user_id)
    ut = db.get(UserTenant, (user_id, tenant_id))
    tenant = db.get(Tenant, tenant_id)
    if not user or not ut or not tenant or user.status != 1 or ut.status != 1:
        return None

    role_codes = list(
        db.scalars(
            select(UserTenantRole.role_code).where(
                UserTenantRole.user_id == user_id, UserTenantRole.tenant_id == tenant_id
            )
        )
    )
    perms: set[str] = set()
    if role_codes:
        perms = set(
            db.scalars(
                select(RolePermission.perm_id)
                .join(Role, Role.role_id == RolePermission.role_id)
                .where(
                    Role.tenant_id == tenant_id,
                    Role.role_code.in_(role_codes),
                    Role.status == 1,
                )
            )
        )

    scope = [
        int(x) for x in (ut.station_scope or "").split(",") if x.strip().isdigit()
    ]
    return Principal(
        user_id=user.user_id,
        username=user.username,
        real_name=user.real_name or user.username,
        tenant_id=tenant_id,
        tenant_name=tenant.tenant_name,
        roles=role_codes,
        permissions=perms,
        station_scope=scope,
    )


def list_users(db: Session, tenant_id: int, keyword: str | None = None) -> list[dict]:
    stmt = (
        select(User, UserTenant.station_scope)
        .join(UserTenant, UserTenant.user_id == User.user_id)
        .where(UserTenant.tenant_id == tenant_id)
    )
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((User.username.like(like)) | (User.real_name.like(like)) | (User.phone.like(like)))
    rows = db.execute(stmt.order_by(User.user_id)).all()

    result: list[dict] = []
    for user, scope in rows:
        roles = list(
            db.scalars(
                select(UserTenantRole.role_code).where(
                    UserTenantRole.user_id == user.user_id, UserTenantRole.tenant_id == tenant_id
                )
            )
        )
        result.append(
            {
                "user_id": user.user_id,
                "username": user.username,
                "real_name": user.real_name,
                "phone": user.phone,
                "status": user.status,
                "roles": roles,
                "station_scope": scope,
                "create_time": user.create_time,
            }
        )
    return result


def list_roles(db: Session, tenant_id: int) -> list[Role]:
    return list(db.scalars(select(Role).where(Role.tenant_id == tenant_id).order_by(Role.role_id)))


def count_username(db: Session, username: str) -> int:
    return int(db.scalar(select(func.count()).select_from(User).where(User.username == username)) or 0)


def list_permissions(db: Session) -> list[Permission]:
    return list(db.scalars(select(Permission).order_by(Permission.perm_group, Permission.sort_no)))
