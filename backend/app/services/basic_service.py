"""基础数据业务：物料 / 分类 / 站点 / 客户 / 用户角色 / 扣杂规则。"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.principal import Principal
from app.core.security import hash_password
from app.models.entities import (
    Customer,
    DeductRule,
    Material,
    MaterialCategory,
    Station,
    User,
    UserTenant,
    UserTenantRole,
)
from app.repositories import customer_repo, material_repo, user_repo
from app.schemas.dto import (
    CategoryUpsert,
    CustomerUpsert,
    DeductRuleUpsert,
    MaterialUpsert,
    StationUpsert,
    UserCreate,
    UserUpdate,
)


# ---------------- 物料 ----------------
def list_materials(db: Session, principal: Principal, keyword: str | None,
                   category_id: int | None, status: int | None) -> list[dict]:
    return material_repo.list_materials(db, principal.tenant_id, keyword, category_id, status)


def create_material(db: Session, principal: Principal, payload: MaterialUpsert) -> dict:
    if material_repo.count_material_code(db, principal.tenant_id, payload.material_code):
        raise ConflictError("物料编码已存在")
    if payload.category_id:
        cat = material_repo.get_category(db, payload.category_id)
        if not cat or (cat.tenant_id not in (None, principal.tenant_id)):
            raise AppError("分类不可用", code="CATEGORY_INVALID")
    m = Material(tenant_id=principal.tenant_id, **payload.model_dump())
    db.add(m)
    db.flush()
    return {"material_id": m.material_id}


def update_material(db: Session, principal: Principal, material_id: int,
                    payload: MaterialUpsert) -> dict:
    m = material_repo.get_material(db, principal.tenant_id, material_id)
    if not m:
        raise NotFoundError("物料不存在")
    if material_repo.count_material_code(db, principal.tenant_id, payload.material_code, material_id):
        raise ConflictError("物料编码已存在")
    for k, v in payload.model_dump().items():
        setattr(m, k, v)
    db.flush()
    return {"material_id": m.material_id}


# ---------------- 分类 ----------------
def category_tree(db: Session, principal: Principal) -> list[dict]:
    flat = material_repo.visible_categories(db, principal.tenant_id)
    nodes = {c["category_id"]: {**c, "children": []} for c in flat}
    roots: list[dict] = []
    for c in flat:
        node = nodes[c["category_id"]]
        parent = nodes.get(c["parent_id"])
        if parent:
            parent["children"].append(node)
        else:
            roots.append(node)
    return roots


def create_category(db: Session, principal: Principal, payload: CategoryUpsert) -> dict:
    parent = None
    if payload.parent_id:
        parent = material_repo.get_category(db, payload.parent_id)
        if not parent or parent.tenant_id not in (None, principal.tenant_id):
            raise AppError("父分类不可用", code="PARENT_INVALID")
    exists = db.scalar(
        select(MaterialCategory).where(
            MaterialCategory.tenant_id == principal.tenant_id,
            MaterialCategory.category_code == payload.category_code,
        )
    )
    if exists:
        raise ConflictError("分类编码已存在")
    cat = MaterialCategory(
        tenant_id=principal.tenant_id,
        parent_id=payload.parent_id,
        category_code=payload.category_code,
        category_name=payload.category_name,
        level=(parent.level + 1) if parent else 1,
        sort_no=(parent.sort_no if parent else 0) + 1,
        is_builtin=0,
        status=1,
    )
    db.add(cat)
    db.flush()
    return {"category_id": cat.category_id}


# ---------------- 站点 ----------------
def list_stations(db: Session, principal: Principal) -> list[dict]:
    rows = db.execute(
        select(Station)
        .where(Station.tenant_id == principal.tenant_id)
        .order_by(Station.station_id)
    ).scalars()
    return [
        {
            "station_id": s.station_id,
            "station_name": s.station_name,
            "station_code": s.station_code,
            "address": s.address,
            "contact_name": s.contact_name,
            "contact_phone": s.contact_phone,
            "status": s.status,
        }
        for s in rows
    ]


def create_station(db: Session, principal: Principal, payload: StationUpsert) -> dict:
    dup = db.scalar(
        select(Station).where(
            Station.tenant_id == principal.tenant_id, Station.station_code == payload.station_code
        )
    )
    if dup:
        raise ConflictError("站点编码已存在")
    s = Station(tenant_id=principal.tenant_id, **payload.model_dump())
    db.add(s)
    db.flush()
    return {"station_id": s.station_id}


def update_station(db: Session, principal: Principal, station_id: int, payload: StationUpsert) -> dict:
    s = db.scalar(
        select(Station).where(
            Station.tenant_id == principal.tenant_id, Station.station_id == station_id
        )
    )
    if not s:
        raise NotFoundError("站点不存在")
    for k, v in payload.model_dump().items():
        setattr(s, k, v)
    db.flush()
    return {"station_id": s.station_id}


# ---------------- 客户 ----------------
def list_customers(db: Session, principal: Principal, keyword: str | None) -> list[dict]:
    return [
        {
            "customer_id": c.customer_id,
            "customer_code": c.customer_code,
            "customer_name": c.customer_name,
            "phone": c.phone,
            "customer_type": c.customer_type,
            "address": c.address,
            "status": c.status,
            "remark": c.remark,
            "create_time": c.create_time,
        }
        for c in customer_repo.list_customers(db, principal.tenant_id, keyword)
    ]


def search_customers(db: Session, principal: Principal, keyword: str | None) -> list[dict]:
    return [
        {
            "customer_id": c.customer_id,
            "customer_name": c.customer_name,
            "phone": c.phone,
            "customer_type": c.customer_type,
        }
        for c in customer_repo.search_customers(db, principal.tenant_id, keyword)
    ]


def create_customer(db: Session, principal: Principal, payload: CustomerUpsert) -> dict:
    if payload.phone:
        dup = customer_repo.find_by_phone(db, principal.tenant_id, payload.phone)
        if dup:
            raise ConflictError(f"手机号已存在，客户：{dup.customer_name}")
    c = Customer(
        tenant_id=principal.tenant_id,
        customer_code=customer_repo.next_customer_code(db, principal.tenant_id),
        customer_name=payload.customer_name,
        phone=payload.phone,
        customer_type=payload.customer_type,
        address=payload.address,
        remark=payload.remark,
        status=1,
    )
    db.add(c)
    db.flush()
    return {"customer_id": c.customer_id}


def update_customer(db: Session, principal: Principal, customer_id: int,
                    payload: CustomerUpsert) -> dict:
    c = customer_repo.get_customer(db, principal.tenant_id, customer_id)
    if not c:
        raise NotFoundError("客户不存在")
    for k, v in payload.model_dump().items():
        setattr(c, k, v)
    db.flush()
    return {"customer_id": c.customer_id}


# ---------------- 用户与角色 ----------------
def list_users(db: Session, principal: Principal, keyword: str | None) -> list[dict]:
    return user_repo.list_users(db, principal.tenant_id, keyword)


def list_roles(db: Session, principal: Principal) -> list[dict]:
    return [
        {
            "role_id": r.role_id,
            "role_code": r.role_code,
            "role_name": r.role_name,
            "is_builtin": r.is_builtin,
            "remark": r.remark,
            "status": r.status,
        }
        for r in user_repo.list_roles(db, principal.tenant_id)
    ]


def list_permissions(db: Session) -> list[dict]:
    return [
        {
            "perm_id": p.perm_id,
            "perm_name": p.perm_name,
            "perm_group": p.perm_group,
            "sort_no": p.sort_no,
        }
        for p in user_repo.list_permissions(db)
    ]


def create_user(db: Session, principal: Principal, payload: UserCreate) -> dict:
    if user_repo.count_username(db, payload.username):
        raise ConflictError("登录名已存在")
    user = User(
        username=payload.username,
        password=hash_password(payload.password),
        real_name=payload.real_name,
        phone=payload.phone,
        status=1,
    )
    db.add(user)
    db.flush()
    db.add(UserTenant(user_id=user.user_id, tenant_id=principal.tenant_id, status=1))
    valid_roles = {r.role_code for r in user_repo.list_roles(db, principal.tenant_id)}
    for code in payload.role_codes:
        if code not in valid_roles:
            raise AppError(f"角色 {code} 不存在", code="ROLE_INVALID")
        db.add(UserTenantRole(user_id=user.user_id, tenant_id=principal.tenant_id, role_code=code))
    if payload.station_scope:
        ut = db.get(UserTenant, (user.user_id, principal.tenant_id))
        if ut:
            ut.station_scope = ",".join(str(x) for x in payload.station_scope)
    db.flush()
    return {"user_id": user.user_id}


def update_user(db: Session, principal: Principal, user_id: int, payload: UserUpdate) -> dict:
    user = user_repo.get_user(db, user_id)
    ut = db.get(UserTenant, (user_id, principal.tenant_id))
    if not user or not ut:
        raise NotFoundError("用户不存在")
    if payload.real_name is not None:
        user.real_name = payload.real_name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.status is not None:
        user.status = payload.status
    if payload.password:
        user.password = hash_password(payload.password)
    if payload.station_scope is not None:
        ut.station_scope = ",".join(str(x) for x in payload.station_scope) or None
    if payload.role_codes is not None:
        valid_roles = {r.role_code for r in user_repo.list_roles(db, principal.tenant_id)}
        for code in payload.role_codes:
            if code not in valid_roles:
                raise AppError(f"角色 {code} 不存在", code="ROLE_INVALID")
        db.execute(
            delete(UserTenantRole).where(
                UserTenantRole.user_id == user_id, UserTenantRole.tenant_id == principal.tenant_id
            )
        )
        for code in payload.role_codes:
            db.add(UserTenantRole(user_id=user_id, tenant_id=principal.tenant_id, role_code=code))
    db.flush()
    return {"user_id": user_id}


# ---------------- 扣杂规则 ----------------
def list_deduct_rules(db: Session, principal: Principal) -> list[dict]:
    return material_repo.list_deduct_rules(db, principal.tenant_id)


def save_deduct_rule(db: Session, principal: Principal, payload: DeductRuleUpsert,
                     rule_id: int | None = None) -> dict:
    if payload.deduct_type in (1, 3) and payload.ratio is None:
        raise AppError("按比例规则必须填写比例", code="RATIO_REQUIRED")
    if payload.deduct_type == 2 and payload.fixed_value is None:
        raise AppError("固定扣重必须填写扣重值", code="FIXED_REQUIRED")
    if rule_id:
        rule = db.scalar(
            select(DeductRule).where(
                DeductRule.tenant_id == principal.tenant_id, DeductRule.rule_id == rule_id
            )
        )
        if not rule:
            raise NotFoundError("规则不存在")
    else:
        rule = DeductRule(tenant_id=principal.tenant_id)
        db.add(rule)
    for k, v in payload.model_dump().items():
        setattr(rule, k, v)
    db.flush()
    return {"rule_id": rule.rule_id}
