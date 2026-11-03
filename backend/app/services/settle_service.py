"""结算业务：勾选批次 → 生成结算单 → 登记付款，保证唯一结算与金额快照。"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.principal import Principal
from app.models.entities import Material, SettleDetail, SettleRecord, WeighItem, WeighTrip
from app.repositories import customer_repo, settle_repo, weigh_repo
from app.schemas.dto import PayRequest, SettleCreate

Q2 = Decimal("0.01")


def _q(v: Decimal) -> Decimal:
    return Decimal(v).quantize(Q2, rounding=ROUND_HALF_UP)


def create_settlement(db: Session, principal: Principal, payload: SettleCreate) -> dict:
    items = settle_repo.items_for_settle(db, principal.tenant_id, payload.item_ids)
    items.sort(key=lambda x: x.item_id)
    if len(items) != len(set(payload.item_ids)):
        raise AppError("部分批次不存在或不属于当前租户", code="ITEM_NOT_FOUND")
    for it in items:
        if it.status != 2:
            raise ConflictError(f"批次 {it.ticket_no} 不是「称重完成」状态，不能结算")
        if it.settle_id:
            raise ConflictError(f"批次 {it.ticket_no} 已结算")

    customer_ids = {it.customer_id for it in items}
    biz_types = {it.biz_type for it in items}
    if len(customer_ids) != 1 or None in customer_ids:
        raise AppError("一次结算只能选择同一客户的批次", code="CUSTOMER_MISMATCH")
    if len(biz_types) != 1:
        raise AppError("收货与发货批次不能合并结算", code="BIZ_TYPE_MISMATCH")
    if any(it.unit_price is None for it in items):
        raise AppError("存在未核价批次，不能结算", code="PRICE_MISSING")

    customer_id = next(iter(customer_ids))
    customer = customer_repo.get_customer(db, principal.tenant_id, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    total_weight = Decimal("0.00")
    total_amount = Decimal("0.00")
    summary: dict[str, dict] = {}
    for it in items:
        weight = Decimal(it.settle_weight or 0)
        amount = _q(weight * Decimal(it.unit_price or 0))
        total_weight += weight
        total_amount += amount
        key = str(it.material_id)
        bucket = summary.setdefault(key, {"weight": 0.0, "amount": 0.0})
        bucket["weight"] = round(bucket["weight"] + float(weight), 2)
        bucket["amount"] = round(bucket["amount"] + float(amount), 2)

    # 物料名称补进汇总快照
    names = dict(
        db.execute(
            select(Material.material_id, Material.material_name).where(
                Material.material_id.in_([int(k) for k in summary])
            )
        ).all()
    )
    material_summary = [
        {"material_id": int(k), "material_name": names.get(int(k), "-"), **v}
        for k, v in summary.items()
    ]

    station_id = None
    first_trip = weigh_repo.get_trip(db, principal.tenant_id, items[0].trip_id)
    if first_trip:
        station_id = first_trip.station_id

    record = SettleRecord(
        tenant_id=principal.tenant_id,
        station_id=station_id,
        settle_no=settle_repo.gen_settle_no(),
        settle_mode=payload.settle_mode,
        trip_id=items[0].trip_id if len({it.trip_id for it in items}) == 1 else None,
        customer_id=customer_id,
        biz_type=next(iter(biz_types)),
        settle_date=date.today(),
        total_settle_weight=_q(total_weight),
        total_amount=_q(total_amount),
        paid_amount=Decimal("0.00"),
        pay_status=0,
        material_summary=material_summary,
        remark=payload.remark,
    )
    db.add(record)
    db.flush()

    for it in items:
        weight = Decimal(it.settle_weight or 0)
        amount = _q(weight * Decimal(it.unit_price or 0))
        db.add(
            SettleDetail(
                tenant_id=principal.tenant_id,
                settle_id=record.settle_id,
                weigh_item_id=it.item_id,
                trip_id=it.trip_id,
                ticket_no=it.ticket_no,
                material_id=it.material_id,
                net_weight=Decimal(it.net_weight or 0),
                deduct_weight=Decimal(it.deduct_weight or 0),
                settle_weight=weight,
                unit_price=Decimal(it.unit_price or 0),
                price_type=it.price_type or 1,
                price_source=it.price_source,
                amount=amount,
                deduct_amount=Decimal("0.00"),
                deduct_reason=None,
                final_amount=amount,
            )
        )
        it.settle_id = record.settle_id
        it.status = 3

    db.flush()
    _sync_trip_status(db, {it.trip_id for it in items})
    return get_settlement(db, principal, record.settle_id)


def pay(db: Session, principal: Principal, settle_id: int, payload: PayRequest) -> dict:
    record = settle_repo.get_record(db, principal.tenant_id, settle_id)
    if not record:
        raise NotFoundError("结算单不存在")
    if record.pay_status == 2:
        raise ConflictError("该结算单已结清")
    remaining = Decimal(record.total_amount) - Decimal(record.paid_amount)
    if Decimal(payload.amount) > remaining:
        raise AppError(f"付款金额超过未结金额 {remaining:.2f} 元", code="OVERPAY")
    record.paid_amount = _q(Decimal(record.paid_amount) + Decimal(payload.amount))
    record.pay_status = 2 if record.paid_amount >= record.total_amount else 1
    if payload.remark:
        record.remark = ((record.remark or "") + f" | 收款：{payload.remark}").strip(" |")
    db.flush()
    return get_settlement(db, principal, settle_id)


def cancel(db: Session, principal: Principal, settle_id: int) -> dict:
    record = settle_repo.get_record(db, principal.tenant_id, settle_id)
    if not record:
        raise NotFoundError("结算单不存在")
    if Decimal(record.paid_amount) > 0:
        raise ConflictError("已发生收付款，不能作废结算单")

    details = list(db.scalars(select(SettleDetail).where(SettleDetail.settle_id == settle_id)))
    trip_ids = set()
    for d in details:
        item = weigh_repo.get_item(db, principal.tenant_id, d.weigh_item_id)
        if item:
            item.status = 2
            item.settle_id = None
            trip_ids.add(item.trip_id)
        db.delete(d)
    db.delete(record)
    db.flush()
    _sync_trip_status(db, trip_ids)
    return {"settle_id": settle_id, "cancelled": True}


def _sync_trip_status(db: Session, trip_ids: set[int]) -> None:
    for tid in trip_ids:
        statuses = list(db.scalars(select(WeighItem.status).where(WeighItem.trip_id == tid)))
        trip = db.get(WeighTrip, tid)
        if not trip or not statuses:
            continue
        if all(s == 3 for s in statuses):
            trip.status = 2
        elif all(s in (2, 3) for s in statuses):
            trip.status = 1
        elif any(s in (0, 1) for s in statuses):
            trip.status = 0
    db.flush()


def get_settlement(db: Session, principal: Principal, settle_id: int) -> dict:
    record = settle_repo.get_record(db, principal.tenant_id, settle_id)
    if not record:
        raise NotFoundError("结算单不存在")
    customer = customer_repo.get_customer(db, principal.tenant_id, record.customer_id)
    return {
        "settle_id": record.settle_id,
        "settle_no": record.settle_no,
        "station_id": record.station_id,
        "customer_id": record.customer_id,
        "customer_name": customer.customer_name if customer else "-",
        "customer_phone": customer.phone if customer else None,
        "biz_type": record.biz_type,
        "settle_mode": record.settle_mode,
        "settle_date": record.settle_date,
        "total_settle_weight": round(float(record.total_settle_weight), 2),
        "total_amount": round(float(record.total_amount), 2),
        "paid_amount": round(float(record.paid_amount), 2),
        "pay_status": record.pay_status,
        "material_summary": record.material_summary,
        "remark": record.remark,
        "create_time": record.create_time,
        "details": settle_repo.record_details(db, settle_id),
    }
