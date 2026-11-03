"""过磅接口：行程、读数、批次核价与称重完成。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.response import ok
from app.core.database import get_db
from app.core.deps import require_perm
from app.core.principal import Principal
from app.repositories import weigh_repo
from app.schemas.dto import CompleteRequest, ItemAdd, PriceRequest, TripCreate
from app.services import weigh_service

router = APIRouter(prefix="/weigh", tags=["过磅"])


@router.post("/trips")
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:create")),
):
    return ok(weigh_service.create_trip(db, principal, payload), "行程已创建")


@router.get("/trips")
def list_trips(
    status: int | None = Query(default=None, ge=0, le=3),
    keyword: str | None = None,
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(weigh_repo.list_trips(db, principal.tenant_id, status=status, keyword=keyword,
                                    start=start, end=end))


@router.get("/trips/active")
def active_trips(
    station_id: int | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    """在场工单（进行中 / 待结算），供过磅工作台并行作业使用。"""
    return ok(weigh_service.list_active_trips(db, principal, station_id))


@router.get("/trips/{trip_id}")
def trip_detail(
    trip_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(weigh_service.get_trip_detail(db, principal, trip_id))


@router.post("/trips/{trip_id}/cancel")
def cancel_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:cancel")),
):
    return ok(weigh_service.cancel_trip(db, principal, trip_id), "工单已作废")


@router.post("/trips/{trip_id}/items")
def add_item(
    trip_id: int,
    payload: ItemAdd,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:item")),
):
    return ok(weigh_service.add_item(db, principal, trip_id, payload), "货物已加入")


@router.get("/items/pending")
def pending_items(
    status: int = Query(default=0, ge=0, le=1),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(weigh_repo.pending_price_items(db, principal.tenant_id, status, keyword))


@router.get("/items/unsettled")
def unsettled_items(
    customer_id: int | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(weigh_repo.unsettled_items(db, principal.tenant_id, customer_id, keyword))


@router.post("/items/{item_id}/price")
def price_item(
    item_id: int,
    payload: PriceRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:item")),
):
    return ok(weigh_service.price_item(db, principal, item_id, payload), "核价完成")


@router.post("/items/{item_id}/complete")
def complete_item(
    item_id: int,
    payload: CompleteRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:item")),
):
    return ok(weigh_service.complete_item(db, principal, item_id, payload), "称重完成")


@router.post("/items/{item_id}/cancel")
def cancel_item(
    item_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:cancel")),
):
    return ok(weigh_service.cancel_item(db, principal, item_id), "批次已作废")
