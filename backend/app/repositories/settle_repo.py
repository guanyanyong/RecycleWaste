"""结算数据访问。"""
from __future__ import annotations

import random
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Customer, Material, SettleDetail, SettleRecord, WeighItem


def gen_settle_no() -> str:
    now = datetime.now()
    return f"ST{now:%Y%m%d%H%M%S}{random.randint(10, 99)}"


def get_record(db: Session, tenant_id: int, settle_id: int) -> SettleRecord | None:
    return db.scalar(
        select(SettleRecord).where(
            SettleRecord.tenant_id == tenant_id, SettleRecord.settle_id == settle_id
        )
    )


def list_records(db: Session, tenant_id: int, keyword: str | None = None,
                 start: date | None = None, end: date | None = None,
                 pay_status: int | None = None, limit: int = 200) -> list[dict]:
    stmt = (
        select(SettleRecord, Customer.customer_name, Customer.phone)
        .outerjoin(Customer, Customer.customer_id == SettleRecord.customer_id)
        .where(SettleRecord.tenant_id == tenant_id)
    )
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(SettleRecord.settle_no.like(like), Customer.customer_name.like(like),
                Customer.phone.like(like))
        )
    if start:
        stmt = stmt.where(SettleRecord.settle_date >= start)
    if end:
        stmt = stmt.where(SettleRecord.settle_date <= end)
    if pay_status is not None:
        stmt = stmt.where(SettleRecord.pay_status == pay_status)
    rows = db.execute(stmt.order_by(SettleRecord.settle_id.desc()).limit(limit)).all()

    result = []
    for rec, cname, phone in rows:
        count = db.scalar(
            select(func.count()).select_from(SettleDetail).where(SettleDetail.settle_id == rec.settle_id)
        )
        result.append(
            {
                "settle_id": rec.settle_id,
                "settle_no": rec.settle_no,
                "station_id": rec.station_id,
                "customer_id": rec.customer_id,
                "customer_name": cname or "-",
                "customer_phone": phone,
                "biz_type": rec.biz_type,
                "settle_mode": rec.settle_mode,
                "settle_date": rec.settle_date,
                "item_count": int(count or 0),
                "total_settle_weight": round(float(rec.total_settle_weight), 2),
                "total_amount": round(float(rec.total_amount), 2),
                "paid_amount": round(float(rec.paid_amount), 2),
                "pay_status": rec.pay_status,
                "remark": rec.remark,
                "create_time": rec.create_time,
            }
        )
    return result


def record_details(db: Session, settle_id: int) -> list[dict]:
    rows = db.execute(
        select(SettleDetail, Material.material_name)
        .outerjoin(Material, Material.material_id == SettleDetail.material_id)
        .where(SettleDetail.settle_id == settle_id)
        .order_by(SettleDetail.detail_id)
    ).all()
    return [
        {
            "detail_id": d.detail_id,
            "weigh_item_id": d.weigh_item_id,
            "ticket_no": d.ticket_no,
            "material_id": d.material_id,
            "material_name": mname or "-",
            "net_weight": round(float(d.net_weight), 2),
            "deduct_weight": round(float(d.deduct_weight), 2),
            "settle_weight": round(float(d.settle_weight), 2),
            "unit_price": round(float(d.unit_price), 4),
            "price_type": d.price_type,
            "price_source": d.price_source,
            "amount": round(float(d.amount), 2),
            "deduct_amount": round(float(d.deduct_amount), 2),
            "deduct_reason": d.deduct_reason,
            "final_amount": round(float(d.final_amount), 2),
        }
        for d, mname in rows
    ]


def items_for_settle(db: Session, tenant_id: int, item_ids: list[int]) -> list[WeighItem]:
    if not item_ids:
        return []
    return list(
        db.scalars(
            select(WeighItem)
            .where(WeighItem.tenant_id == tenant_id, WeighItem.item_id.in_(item_ids))
            .with_for_update()
        )
    )
