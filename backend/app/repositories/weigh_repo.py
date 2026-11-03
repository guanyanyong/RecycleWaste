"""过磅业务数据访问：行程 / 读数 / 货物批次。"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import (
    Customer,
    Material,
    User,
    WeighItem,
    WeighReading,
    WeighTrip,
)


def gen_trip_no(biz_type: int) -> str:
    now = datetime.now()
    return f"{'IN' if biz_type == 1 else 'OUT'}{now:%Y%m%d%H%M%S}{random.randint(10, 99)}"


def gen_ticket_no(trip_no: str, seq: int) -> str:
    return f"{trip_no}-{seq:02d}"


def get_trip(db: Session, tenant_id: int, trip_id: int) -> WeighTrip | None:
    return db.scalar(
        select(WeighTrip).where(WeighTrip.tenant_id == tenant_id, WeighTrip.trip_id == trip_id)
    )


def get_item(db: Session, tenant_id: int, item_id: int) -> WeighItem | None:
    return db.scalar(
        select(WeighItem).where(WeighItem.tenant_id == tenant_id, WeighItem.item_id == item_id)
    )


def list_trips(db: Session, tenant_id: int, *, status: int | None = None,
               keyword: str | None = None, start: date | None = None,
               end: date | None = None, limit: int = 100) -> list[dict]:
    stmt = (
        select(WeighTrip, Customer.customer_name, Customer.phone)
        .outerjoin(Customer, Customer.customer_id == WeighTrip.customer_id)
        .where(WeighTrip.tenant_id == tenant_id)
    )
    if status is not None:
        stmt = stmt.where(WeighTrip.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(WeighTrip.trip_no.like(like), WeighTrip.plate_no.like(like),
                WeighTrip.driver_name.like(like), Customer.customer_name.like(like),
                Customer.phone.like(like))
        )
    if start:
        stmt = stmt.where(WeighTrip.create_time >= datetime.combine(start, datetime.min.time()))
    if end:
        stmt = stmt.where(WeighTrip.create_time < datetime.combine(end + timedelta(days=1), datetime.min.time()))
    rows = db.execute(stmt.order_by(WeighTrip.trip_id.desc()).limit(limit)).all()

    result = []
    for trip, cname, phone in rows:
        items = db.execute(
            select(
                func.count(WeighItem.item_id),
                func.coalesce(func.sum(WeighItem.settle_weight), 0),
                func.coalesce(func.sum(WeighItem.deduct_weight), 0),
            ).where(WeighItem.trip_id == trip.trip_id)
        ).one()
        result.append(
            {
                "trip_id": trip.trip_id,
                "trip_no": trip.trip_no,
                "station_id": trip.station_id,
                "plate_no": trip.plate_no,
                "driver_name": trip.driver_name,
                "customer_id": trip.customer_id,
                "customer_name": cname or "-",
                "customer_phone": phone,
                "biz_type": trip.biz_type,
                "item_count": items[0],
                "total_weight": float(items[1] or 0),
                "total_deduct": float(items[2] or 0),
                "status": trip.status,
                "remark": trip.remark,
                "create_time": trip.create_time,
            }
        )
    return result


def active_trips(db: Session, tenant_id: int, *, station_id: int | None = None,
                 limit: int = 20) -> list[dict]:
    """在场工单：状态为「进行中 / 待结算」的行程，一次性带出各阶段批次进度。

    工作台需要同时盯 3~5 辆车，用单次聚合查询替代逐单查明细，避免 N+1。
    """
    stmt = (
        select(WeighTrip, Customer.customer_name, Customer.phone)
        .outerjoin(Customer, Customer.customer_id == WeighTrip.customer_id)
        .where(WeighTrip.tenant_id == tenant_id, WeighTrip.status.in_((0, 1)))
    )
    if station_id:
        stmt = stmt.where(WeighTrip.station_id == station_id)
    rows = db.execute(stmt.order_by(WeighTrip.trip_id.asc()).limit(limit)).all()
    if not rows:
        return []

    trip_ids = [trip.trip_id for trip, _, _ in rows]
    settled_states = (2, 3)
    agg_rows = db.execute(
        select(
            WeighItem.trip_id,
            func.count(WeighItem.item_id),
            func.coalesce(func.sum(case((WeighItem.status == 0, 1), else_=0)), 0),
            func.coalesce(func.sum(case((WeighItem.status == 1, 1), else_=0)), 0),
            func.coalesce(func.sum(case((WeighItem.status == 2, 1), else_=0)), 0),
            func.coalesce(func.sum(case((WeighItem.status == 3, 1), else_=0)), 0),
            func.coalesce(func.sum(case((WeighItem.status == 4, 1), else_=0)), 0),
            func.coalesce(
                func.sum(case((WeighItem.status.in_(settled_states), WeighItem.settle_weight), else_=0)), 0
            ),
            func.coalesce(
                func.sum(case((WeighItem.status.in_(settled_states),
                               WeighItem.settle_weight * WeighItem.unit_price), else_=0)), 0
            ),
        )
        .where(WeighItem.trip_id.in_(trip_ids))
        .group_by(WeighItem.trip_id)
    ).all()

    stats = {
        tid: {
            "total": int(total or 0),
            "pending_price": int(pending or 0),
            "priced": int(priced or 0),
            "completed": int(completed or 0),
            "settled": int(settled or 0),
            "cancelled": int(cancelled or 0),
            "total_settle_weight": float(weight_sum or 0),
            "total_amount": float(amount_sum or 0),
        }
        for tid, total, pending, priced, completed, settled, cancelled, weight_sum, amount_sum in agg_rows
    }

    now = datetime.now()
    result = []
    for trip, cname, phone in rows:
        s = stats.get(trip.trip_id) or {
            "total": 0, "pending_price": 0, "priced": 0, "completed": 0,
            "settled": 0, "cancelled": 0, "total_settle_weight": 0.0, "total_amount": 0.0,
        }
        effective = max(s["total"] - s["cancelled"], 0)
        done = s["completed"] + s["settled"]
        elapsed = int((now - trip.create_time).total_seconds() // 60) if trip.create_time else 0
        result.append(
            {
                "trip_id": trip.trip_id,
                "trip_no": trip.trip_no,
                "station_id": trip.station_id,
                "plate_no": trip.plate_no,
                "driver_name": trip.driver_name,
                "customer_id": trip.customer_id,
                "customer_name": cname or "-",
                "customer_phone": phone,
                "biz_type": trip.biz_type,
                "status": trip.status,
                "item_count": s["total"],
                "effective_count": effective,
                "pending_price": s["pending_price"],
                "priced": s["priced"],
                "completed": s["completed"],
                "settled": s["settled"],
                "cancelled": s["cancelled"],
                "progress": round(done / effective * 100) if effective else 0,
                "total_settle_weight": round(s["total_settle_weight"], 2),
                "total_amount": round(s["total_amount"], 2),
                "elapsed_minutes": max(elapsed, 0),
                "create_time": trip.create_time,
            }
        )
    return result


def count_active_trips(db: Session, tenant_id: int) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(WeighTrip).where(
                WeighTrip.tenant_id == tenant_id, WeighTrip.status.in_((0, 1))
            )
        )
        or 0
    )


def find_active_by_plate(db: Session, tenant_id: int, plate_no: str) -> WeighTrip | None:
    return db.scalar(
        select(WeighTrip)
        .where(
            WeighTrip.tenant_id == tenant_id,
            WeighTrip.status.in_((0, 1)),
            func.upper(WeighTrip.plate_no) == plate_no.upper(),
        )
        .order_by(WeighTrip.trip_id.desc())
        .limit(1)
    )


def trip_items(db: Session, trip_id: int) -> list[dict]:
    rows = db.execute(
        select(WeighItem, Material.material_name, Material.unit)
        .outerjoin(Material, Material.material_id == WeighItem.material_id)
        .where(WeighItem.trip_id == trip_id)
        .order_by(WeighItem.seq)
    ).all()
    return [
        {
            "item_id": it.item_id,
            "trip_id": it.trip_id,
            "seq": it.seq,
            "ticket_no": it.ticket_no,
            "material_id": it.material_id,
            "material_name": mname or "-",
            "unit": unit or "吨",
            "customer_id": it.customer_id,
            "biz_type": it.biz_type,
            "weigh_mode": it.weigh_mode,
            "start_reading_id": it.start_reading_id,
            "end_reading_id": it.end_reading_id,
            "start_weight": _f(it.start_weight),
            "end_weight": _f(it.end_weight),
            "net_weight": _f(it.net_weight),
            "deduct_weight": _f(it.deduct_weight),
            "deduct_preview": _deduct_preview(it),
            "deduct_detail": it.deduct_detail,
            "settle_weight": _f(it.settle_weight),
            "unit_price": _f(it.unit_price, 4),
            "price_type": it.price_type,
            "price_source": it.price_source,
            "deduct_rule_snapshot": it.deduct_rule_snapshot,
            "settle_id": it.settle_id,
            "status": it.status,
            "remark": it.remark,
            "create_time": it.create_time,
            "update_time": it.update_time,
        }
        for it, mname, unit in rows
    ]


def trip_readings(db: Session, trip_id: int) -> list[dict]:
    rows = db.execute(
        select(WeighReading, User.real_name)
        .outerjoin(User, User.user_id == WeighReading.operator_id)
        .where(WeighReading.trip_id == trip_id)
        .order_by(WeighReading.seq)
    ).all()
    return [
        {
            "reading_id": r.reading_id,
            "seq": r.seq,
            "weight": _f(r.weight),
            "reading_time": r.reading_time,
            "operator_name": name or "-",
            "device_id": r.device_id,
        }
        for r, name in rows
    ]


def max_item_seq(db: Session, trip_id: int) -> int:
    return int(db.scalar(select(func.max(WeighItem.seq)).where(WeighItem.trip_id == trip_id)) or 0)


def max_reading_seq(db: Session, trip_id: int) -> int:
    return int(db.scalar(select(func.max(WeighReading.seq)).where(WeighReading.trip_id == trip_id)) or 0)


def get_reading(db: Session, tenant_id: int, trip_id: int, reading_id: int) -> WeighReading | None:
    return db.scalar(
        select(WeighReading).where(
            WeighReading.tenant_id == tenant_id,
            WeighReading.trip_id == trip_id,
            WeighReading.reading_id == reading_id,
        )
    )


def pending_price_items(db: Session, tenant_id: int, status: int = 0, keyword: str | None = None,
                        limit: int = 200) -> list[dict]:
    stmt = (
        select(WeighItem, Material.material_name, WeighTrip.trip_no, WeighTrip.plate_no,
               Customer.customer_name)
        .join(WeighTrip, WeighTrip.trip_id == WeighItem.trip_id)
        .outerjoin(Material, Material.material_id == WeighItem.material_id)
        .outerjoin(Customer, Customer.customer_id == WeighItem.customer_id)
        .where(WeighItem.tenant_id == tenant_id, WeighItem.status == status)
    )
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(WeighItem.ticket_no.like(like), Material.material_name.like(like),
                Customer.customer_name.like(like), WeighTrip.plate_no.like(like))
        )
    rows = db.execute(stmt.order_by(WeighItem.item_id.desc()).limit(limit)).all()
    return [
        {
            "item_id": it.item_id,
            "ticket_no": it.ticket_no,
            "trip_id": it.trip_id,
            "trip_no": tno,
            "plate_no": plate,
            "customer_id": it.customer_id,
            "customer_name": cname or "-",
            "material_id": it.material_id,
            "material_name": mname or "-",
            "weigh_mode": it.weigh_mode,
            "start_weight": _f(it.start_weight),
            "end_weight": _f(it.end_weight),
            "net_weight": _f(it.net_weight),
            "deduct_weight": _f(it.deduct_weight),
            "unit_price": _f(it.unit_price, 4),
            "price_type": it.price_type,
            "status": it.status,
            "create_time": it.create_time,
        }
        for it, mname, tno, plate, cname in rows
    ]


def unsettled_items(db: Session, tenant_id: int, customer_id: int | None = None,
                    keyword: str | None = None, limit: int = 300) -> list[dict]:
    stmt = (
        select(WeighItem, Material.material_name, WeighTrip.trip_no, Customer.customer_name,
               Customer.phone)
        .join(WeighTrip, WeighTrip.trip_id == WeighItem.trip_id)
        .outerjoin(Material, Material.material_id == WeighItem.material_id)
        .outerjoin(Customer, Customer.customer_id == WeighItem.customer_id)
        .where(WeighItem.tenant_id == tenant_id, WeighItem.status == 2)
    )
    if customer_id:
        stmt = stmt.where(WeighItem.customer_id == customer_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(WeighItem.ticket_no.like(like), Customer.customer_name.like(like),
                Material.material_name.like(like))
        )
    rows = db.execute(stmt.order_by(WeighItem.item_id.desc()).limit(limit)).all()
    return [
        {
            "item_id": it.item_id,
            "ticket_no": it.ticket_no,
            "trip_id": it.trip_id,
            "trip_no": tno,
            "customer_id": it.customer_id,
            "customer_name": cname or "-",
            "customer_phone": phone,
            "material_id": it.material_id,
            "material_name": mname or "-",
            "net_weight": _f(it.net_weight),
            "deduct_weight": _f(it.deduct_weight),
            "settle_weight": _f(it.settle_weight),
            "unit_price": _f(it.unit_price, 4),
            "price_type": it.price_type,
            "amount": float((it.settle_weight or Decimal(0)) * (it.unit_price or Decimal(0))),
            "biz_type": it.biz_type,
            "create_time": it.create_time,
        }
        for it, mname, tno, cname, phone in rows
    ]


def _f(value: Decimal | None, digits: int = 2) -> float | None:
    return None if value is None else round(float(value), digits)


def _deduct_preview(item: WeighItem) -> float | None:
    """两次过磅在核价后、皮重前，按规则快照预估扣重，供界面提示（不落库）。"""
    snap = item.deduct_rule_snapshot or {}
    if not snap or item.status != 1:
        return None
    base = item.start_weight if (snap.get("calc_base") == 1 or item.net_weight is None) else item.net_weight
    dtype = snap.get("deduct_type")
    if dtype == 2 and snap.get("fixed_value") is not None:
        value = Decimal(str(snap["fixed_value"]))
    elif dtype == 1 and snap.get("ratio") is not None:
        value = Decimal(base) * Decimal(str(snap["ratio"]))
    else:
        return 0.0
    return round(float(min(value, Decimal(base))), 2)
