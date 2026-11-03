"""基础数据接口：物料、分类、扣杂规则、站点、客户、用户。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.response import ok
from app.core.database import get_db
from app.core.deps import require_perm
from app.core.principal import Principal
from app.schemas.dto import (
    CategoryUpsert,
    CustomerUpsert,
    DeductRuleUpsert,
    MaterialUpsert,
    StationUpsert,
    UserCreate,
    UserUpdate,
)
from app.services import basic_service

router = APIRouter(tags=["基础数据"])


# ---------- 物料 ----------
@router.get("/materials")
def materials(
    keyword: str | None = None,
    category_id: int | None = None,
    status: int | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(basic_service.list_materials(db, principal, keyword, category_id, status))


@router.post("/materials")
def create_material(
    payload: MaterialUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("material:manage")),
):
    return ok(basic_service.create_material(db, principal, payload), "物料已创建")


@router.put("/materials/{material_id}")
def update_material(
    material_id: int,
    payload: MaterialUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("material:manage")),
):
    return ok(basic_service.update_material(db, principal, material_id, payload), "物料已更新")


@router.get("/categories/tree")
def categories(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(basic_service.category_tree(db, principal))


@router.post("/categories")
def create_category(
    payload: CategoryUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("material:manage")),
):
    return ok(basic_service.create_category(db, principal, payload), "分类已创建")


# ---------- 扣杂规则 ----------
@router.get("/deduct-rules")
def deduct_rules(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("deduct:config")),
):
    return ok(basic_service.list_deduct_rules(db, principal))


@router.post("/deduct-rules")
def save_deduct_rule(
    payload: DeductRuleUpsert,
    rule_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("deduct:config")),
):
    return ok(basic_service.save_deduct_rule(db, principal, payload, rule_id), "规则已保存")


# ---------- 站点 ----------
@router.get("/stations")
def stations(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(basic_service.list_stations(db, principal))


@router.post("/stations")
def create_station(
    payload: StationUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("station:manage")),
):
    return ok(basic_service.create_station(db, principal, payload), "站点已创建")


@router.put("/stations/{station_id}")
def update_station(
    station_id: int,
    payload: StationUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("station:manage")),
):
    return ok(basic_service.update_station(db, principal, station_id, payload), "站点已更新")


# ---------- 客户 ----------
@router.get("/customers")
def customers(
    keyword: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(basic_service.list_customers(db, principal, keyword))


@router.get("/customers/search")
def search_customers(
    keyword: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:create")),
):
    return ok(basic_service.search_customers(db, principal, keyword))


@router.post("/customers")
def create_customer(
    payload: CustomerUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:create")),
):
    return ok(basic_service.create_customer(db, principal, payload), "客户已创建")


@router.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    payload: CustomerUpsert,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:create")),
):
    return ok(basic_service.update_customer(db, principal, customer_id, payload), "客户已更新")


# ---------- 用户与角色 ----------
@router.get("/users")
def users(
    keyword: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("user:manage")),
):
    return ok(basic_service.list_users(db, principal, keyword))


@router.post("/users")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("user:manage")),
):
    return ok(basic_service.create_user(db, principal, payload), "用户已创建")


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("user:manage")),
):
    return ok(basic_service.update_user(db, principal, user_id, payload), "用户已更新")


@router.get("/roles")
def roles(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("user:manage")),
):
    return ok(basic_service.list_roles(db, principal))


@router.get("/permissions")
def permissions(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("user:manage")),
):
    return ok(basic_service.list_permissions(db))
