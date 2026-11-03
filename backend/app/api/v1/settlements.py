"""结算接口。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.response import ok
from app.core.database import get_db
from app.core.deps import require_perm
from app.core.principal import Principal
from app.repositories import settle_repo
from app.schemas.dto import PayRequest, SettleCreate
from app.services import settle_service

router = APIRouter(prefix="/settlements", tags=["结算"])


@router.post("")
def create(
    payload: SettleCreate,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("settle:create")),
):
    return ok(settle_service.create_settlement(db, principal, payload), "结算单已生成")


@router.get("")
def list_records(
    keyword: str | None = None,
    start: date | None = None,
    end: date | None = None,
    pay_status: int | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("settle:view")),
):
    return ok(settle_repo.list_records(db, principal.tenant_id, keyword, start, end, pay_status))


@router.get("/{settle_id}")
def detail(
    settle_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("settle:view")),
):
    return ok(settle_service.get_settlement(db, principal, settle_id))


@router.post("/{settle_id}/pay")
def pay(
    settle_id: int,
    payload: PayRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("settle:pay")),
):
    return ok(settle_service.pay(db, principal, settle_id, payload), "收付款已登记")


@router.post("/{settle_id}/cancel")
def cancel(
    settle_id: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("settle:cancel")),
):
    return ok(settle_service.cancel(db, principal, settle_id), "结算单已作废")
