"""看板与报表统计查询。"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Customer, Material, SettleRecord, WeighItem, WeighTrip


def _day_start(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time())


def overview(db: Session, tenant_id: int, today: date) -> dict:
    start = _day_start(today)
    end = start + timedelta(days=1)

    today_trips = int(
        db.scalar(
            select(func.count()).select_from(WeighTrip).where(
                WeighTrip.tenant_id == tenant_id,
                WeighTrip.create_time >= start,
                WeighTrip.create_time < end,
            )
        ) or 0
    )
    today_weight = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(WeighItem.settle_weight), 0)).where(
                WeighItem.tenant_id == tenant_id,
                WeighItem.status.in_([2, 3]),
                WeighItem.update_time >= start,
                WeighItem.update_time < end,
            )
        ) or 0
    )
    today_amount = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(SettleRecord.total_amount), 0)).where(
                SettleRecord.tenant_id == tenant_id, SettleRecord.settle_date == today
            )
        ) or 0
    )
    pending_price = int(
        db.scalar(
            select(func.count()).select_from(WeighItem).where(
                WeighItem.tenant_id == tenant_id, WeighItem.status.in_([0, 1])
            )
        ) or 0
    )
    pending_settle = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(WeighItem.settle_weight), 0)).where(
                WeighItem.tenant_id == tenant_id, WeighItem.status == 2
            )
        ) or 0
    )
    unpaid_amount = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(SettleRecord.total_amount - SettleRecord.paid_amount), 0)).where(
                SettleRecord.tenant_id == tenant_id, SettleRecord.pay_status != 2
            )
        ) or 0
    )
    customer_count = int(
        db.scalar(
            select(func.count()).select_from(Customer).where(
                Customer.tenant_id == tenant_id, Customer.status == 1
            )
        ) or 0
    )
    return {
        "today_trips": today_trips,
        "today_weight": round(float(today_weight), 2),
        "today_amount": round(float(today_amount), 2),
        "pending_price": pending_price,
        "pending_settle_weight": round(float(pending_settle), 2),
        "unpaid_amount": round(float(unpaid_amount), 2),
        "customer_count": customer_count,
    }


def trend(db: Session, tenant_id: int, days: int = 7) -> list[dict]:
    today = date.today()
    start = today - timedelta(days=days - 1)
    rows = db.execute(
        select(
            func.date(WeighItem.update_time).label("d"),
            func.coalesce(func.sum(WeighItem.settle_weight), 0),
            func.count(WeighItem.item_id),
        )
        .where(
            WeighItem.tenant_id == tenant_id,
            WeighItem.status.in_([2, 3]),
            WeighItem.update_time >= _day_start(start),
        )
        .group_by(func.date(WeighItem.update_time))
    ).all()
    bucket = {str(r[0]): (float(r[1] or 0), int(r[2] or 0)) for r in rows}

    amount_rows = db.execute(
        select(func.date(SettleRecord.settle_date), func.coalesce(func.sum(SettleRecord.total_amount), 0))
        .where(SettleRecord.tenant_id == tenant_id, SettleRecord.settle_date >= start)
        .group_by(func.date(SettleRecord.settle_date))
    ).all()
    amount_bucket = {str(r[0]): float(r[1] or 0) for r in amount_rows}

    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.isoformat()
        weight, cnt = bucket.get(key, (0.0, 0))
        result.append(
            {
                "date": d.strftime("%m-%d"),
                "weight": round(weight, 2),
                "count": cnt,
                "amount": round(amount_bucket.get(key, 0.0), 2),
            }
        )
    return result


def material_distribution(db: Session, tenant_id: int, days: int = 30) -> list[dict]:
    start = _day_start(date.today() - timedelta(days=days - 1))
    rows = db.execute(
        select(Material.material_name, func.coalesce(func.sum(WeighItem.settle_weight), 0))
        .join(Material, Material.material_id == WeighItem.material_id)
        .where(
            WeighItem.tenant_id == tenant_id,
            WeighItem.status.in_([2, 3]),
            WeighItem.update_time >= start,
        )
        .group_by(Material.material_name)
        .order_by(func.sum(WeighItem.settle_weight).desc())
        .limit(8)
    ).all()
    return [{"name": r[0], "value": round(float(r[1] or 0), 2)} for r in rows]


def station_distribution(db: Session, tenant_id: int) -> list[dict]:
    rows = db.execute(
        select(
            WeighTrip.station_id,
            func.count(WeighTrip.trip_id),
            func.coalesce(func.sum(WeighItem.settle_weight), 0),
        )
        .outerjoin(WeighItem, WeighItem.trip_id == WeighTrip.trip_id)
        .where(WeighTrip.tenant_id == tenant_id)
        .group_by(WeighTrip.station_id)
    ).all()
    return [
        {"station_id": r[0], "count": int(r[1] or 0), "weight": round(float(r[2] or 0), 2)}
        for r in rows
    ]


def daily_report(db: Session, tenant_id: int, start: date, end: date) -> list[dict]:
    rows = db.execute(
        select(
            Material.material_name,
            func.coalesce(func.sum(WeighItem.net_weight), 0),
            func.coalesce(func.sum(WeighItem.deduct_weight), 0),
            func.coalesce(func.sum(WeighItem.settle_weight), 0),
            func.count(WeighItem.item_id),
        )
        .join(Material, Material.material_id == WeighItem.material_id)
        .where(
            WeighItem.tenant_id == tenant_id,
            WeighItem.status.in_([2, 3]),
            WeighItem.update_time >= _day_start(start),
            WeighItem.update_time < _day_start(end + timedelta(days=1)),
        )
        .group_by(Material.material_name)
        .order_by(func.sum(WeighItem.settle_weight).desc())
    ).all()
    return [
        {
            "material_name": r[0],
            "net_weight": round(float(r[1] or 0), 2),
            "deduct_weight": round(float(r[2] or 0), 2),
            "settle_weight": round(float(r[3] or 0), 2),
            "item_count": int(r[4] or 0),
        }
        for r in rows
    ]
