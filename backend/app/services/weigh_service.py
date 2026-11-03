"""过磅核心业务：行程 → 批次 → 核价 → 称重完成，严格的状态机与快照原则。"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.principal import Principal
from app.models.entities import Customer, Material, WeighItem, WeighReading, WeighTrip
from app.repositories import customer_repo, material_repo, weigh_repo
from app.schemas.dto import CompleteRequest, ItemAdd, PriceRequest, TripCreate

Q2 = Decimal("0.01")
Q4 = Decimal("0.0001")
ITEM_STATUS = {
    0: "新建", 1: "已核价", 2: "称重完成", 3: "已结算", 4: "作废",
}
# 现场同时在场车辆上限（真实作业通常 3~5 辆，留出高峰冗余）
MAX_ACTIVE_TRIPS = 12


def _q(value: Decimal, q: Decimal = Q2) -> Decimal:
    return Decimal(value).quantize(q, rounding=ROUND_HALF_UP)


def _ensure_station(principal: Principal, station_id: int) -> None:
    if not principal.station_allowed(station_id):
        raise AppError("当前账号无权操作该站点", code="STATION_FORBIDDEN", status_code=403)


def _guard_parallel_capacity(db: Session, tenant_id: int) -> None:
    """控制在场工单并发数量，避免开单不收敛导致工作台堆满无效工单。"""
    if weigh_repo.count_active_trips(db, tenant_id) >= MAX_ACTIVE_TRIPS:
        raise ConflictError(
            f"在场工单已达并行上限 {MAX_ACTIVE_TRIPS} 单，请先完成或作废部分工单"
        )


def _guard_plate_duplicate(db: Session, tenant_id: int, plate_no: str | None) -> None:
    """同一车牌不允许存在两张未结束的工单，防止重复过磅生成双份磅单。"""
    plate = (plate_no or "").strip()
    if not plate:
        return
    dup = weigh_repo.find_active_by_plate(db, tenant_id, plate)
    if dup:
        raise ConflictError(f"车牌 {plate} 已有在场工单 {dup.trip_no}，请先完成该工单")


def list_active_trips(db: Session, principal: Principal, station_id: int | None = None) -> dict:
    trips = weigh_repo.active_trips(db, principal.tenant_id, station_id=station_id,
                                    limit=MAX_ACTIVE_TRIPS + 8)
    return {
        "trips": trips,
        "active_count": len(trips),
        "max_active": MAX_ACTIVE_TRIPS,
        "pending_price_total": sum(t["pending_price"] for t in trips),
        "pending_weight": round(sum(t["total_settle_weight"] for t in trips), 2),
    }


def cancel_trip(db: Session, principal: Principal, trip_id: int) -> dict:
    """作废整张工单：仅允许对没有有效批次的工单操作（误开单 / 车辆临时离场）。"""
    trip = weigh_repo.get_trip(db, principal.tenant_id, trip_id)
    if not trip:
        raise NotFoundError("行程不存在")
    _ensure_station(principal, trip.station_id)
    if trip.status == 2:
        raise ConflictError("行程已完成结算，不能作废")
    if trip.status == 3:
        raise ConflictError("行程已作废，无需重复操作")
    statuses = list(db.scalars(select(WeighItem.status).where(WeighItem.trip_id == trip_id)))
    if any(s != 4 for s in statuses):
        raise ConflictError("行程下存在有效批次，请先作废批次或将批次转入结算")
    trip.status = 3
    db.flush()
    return {"trip_id": trip.trip_id, "trip_no": trip.trip_no, "status": trip.status}


def create_trip(db: Session, principal: Principal, payload: TripCreate) -> dict:
    _ensure_station(principal, payload.station_id)
    _guard_parallel_capacity(db, principal.tenant_id)
    _guard_plate_duplicate(db, principal.tenant_id, payload.plate_no)

    customer_id = payload.customer_id
    if customer_id:
        customer = customer_repo.get_customer(db, principal.tenant_id, customer_id)
        if not customer:
            raise NotFoundError("客户不存在")
    elif payload.customer_phone:
        customer = customer_repo.find_by_phone(db, principal.tenant_id, payload.customer_phone)
        if not customer:
            if not payload.customer_name:
                raise AppError("新客户需要填写姓名", code="CUSTOMER_NAME_REQUIRED")
            customer = Customer(
                tenant_id=principal.tenant_id,
                customer_code=customer_repo.next_customer_code(db, principal.tenant_id),
                customer_name=payload.customer_name,
                phone=payload.customer_phone,
                customer_type=1,
                status=1,
            )
            db.add(customer)
            db.flush()
        customer_id = customer.customer_id
    elif payload.customer_name:
        customer = Customer(
            tenant_id=principal.tenant_id,
            customer_code=customer_repo.next_customer_code(db, principal.tenant_id),
            customer_name=payload.customer_name,
            customer_type=1,
            status=1,
        )
        db.add(customer)
        db.flush()
        customer_id = customer.customer_id
    else:
        raise AppError("请先识别客户（姓名或手机号）", code="CUSTOMER_REQUIRED")

    trip = WeighTrip(
        tenant_id=principal.tenant_id,
        station_id=payload.station_id,
        trip_no=weigh_repo.gen_trip_no(payload.biz_type),
        plate_no=payload.plate_no,
        driver_name=payload.driver_name,
        customer_id=customer_id,
        biz_type=payload.biz_type,
        item_count=0,
        status=0,
        remark=payload.remark,
    )
    db.add(trip)
    db.flush()
    return get_trip_detail(db, principal, trip.trip_id)


def add_item(db: Session, principal: Principal, trip_id: int, payload: ItemAdd) -> dict:
    trip = weigh_repo.get_trip(db, principal.tenant_id, trip_id)
    if not trip:
        raise NotFoundError("行程不存在")
    if trip.status not in (0, 1):
        raise ConflictError("该行程已结算或作废，不能继续过磅")
    _ensure_station(principal, trip.station_id)

    material = material_repo.get_material(db, principal.tenant_id, payload.material_id)
    if not material or material.status != 1:
        raise AppError("物料不存在或已停用", code="MATERIAL_INVALID")

    now = datetime.now()
    if payload.reuse_reading_id:
        reading = weigh_repo.get_reading(db, principal.tenant_id, trip_id, payload.reuse_reading_id)
        if not reading:
            raise AppError("复用的读数不属于当前行程", code="READING_INVALID")
        weight = Decimal(reading.weight)
        start_reading_id = reading.reading_id
    else:
        if payload.weight is None:
            raise AppError("请录入地磅读数", code="WEIGHT_REQUIRED")
        seq = weigh_repo.max_reading_seq(db, trip_id) + 1
        reading = WeighReading(
            tenant_id=principal.tenant_id,
            trip_id=trip_id,
            seq=seq,
            weight=_q(payload.weight),
            reading_time=now,
            operator_id=principal.user_id,
        )
        db.add(reading)
        db.flush()
        weight = _q(payload.weight)
        start_reading_id = reading.reading_id

    item_seq = weigh_repo.max_item_seq(db, trip_id) + 1
    item = WeighItem(
        tenant_id=principal.tenant_id,
        trip_id=trip_id,
        seq=item_seq,
        ticket_no=weigh_repo.gen_ticket_no(trip.trip_no, item_seq),
        material_id=material.material_id,
        customer_id=trip.customer_id,
        biz_type=trip.biz_type,
        weigh_mode=payload.weigh_mode,
        start_reading_id=start_reading_id,
        start_weight=weight,
        net_weight=weight if payload.weigh_mode == 2 else None,
        deduct_weight=Decimal("0.00"),
        settle_weight=weight if payload.weigh_mode == 2 else None,
        status=0,
    )
    db.add(item)
    trip.item_count = item_seq
    if trip.status == 1:
        trip.status = 0
    db.flush()
    return get_trip_detail(db, principal, trip_id)


def price_item(db: Session, principal: Principal, item_id: int, payload: PriceRequest) -> dict:
    item = weigh_repo.get_item(db, principal.tenant_id, item_id)
    if not item:
        raise NotFoundError("货物批次不存在")
    if item.status != 0:
        raise ConflictError(f"当前状态为「{ITEM_STATUS.get(item.status)}」，只有新建批次可以核价")
    if payload.price_type == 2 and not payload.price_source:
        raise AppError("浮动价必须填写价格来源/批次", code="PRICE_SOURCE_REQUIRED")
    if payload.deduct_type == 1 and payload.deduct_ratio is None:
        raise AppError("按比例扣重必须填写扣重比例", code="DEDUCT_RATIO_REQUIRED")
    if payload.deduct_type == 2 and payload.deduct_fixed is None:
        raise AppError("按固定重量扣重必须填写扣重值", code="DEDUCT_FIXED_REQUIRED")

    snapshot = {
        "deduct_type": payload.deduct_type,
        "ratio": float(payload.deduct_ratio) if payload.deduct_ratio is not None else None,
        "fixed_value": float(payload.deduct_fixed) if payload.deduct_fixed is not None else None,
        "calc_base": payload.calc_base,
    }

    item.unit_price = _q(payload.unit_price, Q4)
    item.price_type = payload.price_type
    item.price_source = payload.price_source
    item.deduct_rule_snapshot = snapshot
    item.pricing_user_id = principal.user_id
    item.pricing_time = datetime.now()
    item.status = 1

    # 单次过磅此时净重已知，立即算出扣重与结算净重；两次过磅待皮重完成再算
    if item.net_weight is not None:
        _apply_deduct(item, Decimal(item.net_weight), Decimal(item.start_weight))
    db.flush()
    return item_payload(item)


def complete_item(db: Session, principal: Principal, item_id: int, payload: CompleteRequest) -> dict:
    item = weigh_repo.get_item(db, principal.tenant_id, item_id)
    if not item:
        raise NotFoundError("货物批次不存在")
    if item.status != 1:
        raise ConflictError(f"当前状态为「{ITEM_STATUS.get(item.status)}」，只有已核价批次可以完成称重")
    trip = weigh_repo.get_trip(db, principal.tenant_id, item.trip_id)
    if not trip:
        raise NotFoundError("行程不存在")
    _ensure_station(principal, trip.station_id)

    if item.weigh_mode == 1:
        if payload.end_weight is None:
            raise AppError("两次过磅模式必须录入皮重", code="TARE_REQUIRED")
        end_weight = _q(payload.end_weight)
        if end_weight >= Decimal(item.start_weight):
            raise AppError("皮重必须小于毛重", code="INVALID_TARE")
        seq = weigh_repo.max_reading_seq(db, trip.trip_id) + 1
        reading = WeighReading(
            tenant_id=principal.tenant_id,
            trip_id=trip.trip_id,
            seq=seq,
            weight=end_weight,
            reading_time=datetime.now(),
            operator_id=principal.user_id,
        )
        db.add(reading)
        db.flush()
        item.end_reading_id = reading.reading_id
        item.end_weight = end_weight
        item.net_weight = _q(Decimal(item.start_weight) - end_weight)
    else:
        if payload.end_weight is not None:
            raise AppError("单次过磅模式不需要录入皮重", code="TARE_NOT_ALLOWED")
        item.end_weight = None
        item.net_weight = _q(Decimal(item.start_weight))

    _apply_deduct(item, Decimal(item.net_weight), Decimal(item.start_weight))
    item.status = 2
    db.flush()

    # 行程内全部批次称重完成 → 行程状态置为「称重完成」
    siblings = list(
        db.scalars(select(WeighItem.status).where(WeighItem.trip_id == trip.trip_id))
    )
    if siblings and all(s in (2, 3) for s in siblings):
        trip.status = 1
    db.flush()
    return item_payload(item)


def cancel_item(db: Session, principal: Principal, item_id: int) -> dict:
    item = weigh_repo.get_item(db, principal.tenant_id, item_id)
    if not item:
        raise NotFoundError("货物批次不存在")
    if item.settle_id:
        raise ConflictError("该批次已进入结算，请先作废结算单")
    if item.status in (3, 4):
        raise ConflictError("该批次已结算或已作废，不能再次作废")
    item.status = 4
    db.flush()
    return item_payload(item)


def _apply_deduct(item: WeighItem, net: Decimal, gross: Decimal) -> None:
    snap = item.deduct_rule_snapshot or {}
    deduct_type = int(snap.get("deduct_type") or 1)
    base = gross if int(snap.get("calc_base") or 2) == 1 else net
    deduct = Decimal("0.00")
    detail = {"deduct_type": deduct_type, "calc_base": int(snap.get("calc_base") or 2)}

    if deduct_type == 1 and snap.get("ratio") is not None:
        deduct = _q(base * Decimal(str(snap["ratio"])))
        detail["ratio"] = snap["ratio"]
    elif deduct_type == 2 and snap.get("fixed_value") is not None:
        deduct = _q(Decimal(str(snap["fixed_value"])))
        detail["fixed_value"] = snap["fixed_value"]
    elif deduct_type == 3 and snap.get("ratio") is not None:
        deduct = Decimal("0.00")
        detail["ratio"] = snap["ratio"]
        detail["note"] = "按比例扣款，不计扣重"

    if deduct < 0:
        deduct = Decimal("0.00")
    if deduct > net:
        deduct = net
    item.deduct_weight = deduct
    item.deduct_detail = detail
    item.settle_weight = _q(net - deduct)


def item_payload(item: WeighItem) -> dict:
    return {
        "item_id": item.item_id,
        "ticket_no": item.ticket_no,
        "status": item.status,
        "status_text": ITEM_STATUS.get(item.status),
        "start_reading_id": item.start_reading_id,
        "end_reading_id": item.end_reading_id,
        "start_weight": float(item.start_weight) if item.start_weight is not None else None,
        "end_weight": float(item.end_weight) if item.end_weight is not None else None,
        "net_weight": float(item.net_weight) if item.net_weight is not None else None,
        "deduct_weight": float(item.deduct_weight or 0),
        "settle_weight": float(item.settle_weight) if item.settle_weight is not None else None,
        "unit_price": float(item.unit_price) if item.unit_price else None,
    }


def get_trip_detail(db: Session, principal: Principal, trip_id: int) -> dict:
    trip = weigh_repo.get_trip(db, principal.tenant_id, trip_id)
    if not trip:
        raise NotFoundError("行程不存在")
    customer = customer_repo.get_customer(db, principal.tenant_id, trip.customer_id) if trip.customer_id else None
    items = weigh_repo.trip_items(db, trip_id)
    readings = weigh_repo.trip_readings(db, trip_id)

    total_settle = sum(Decimal(str(i["settle_weight"] or 0)) for i in items if i["status"] in (2, 3))
    total_amount = sum(
        Decimal(str(i["settle_weight"] or 0)) * Decimal(str(i["unit_price"] or 0))
        for i in items if i["status"] in (2, 3)
    )
    return {
        "trip": {
            "trip_id": trip.trip_id,
            "trip_no": trip.trip_no,
            "station_id": trip.station_id,
            "plate_no": trip.plate_no,
            "driver_name": trip.driver_name,
            "customer_id": trip.customer_id,
            "customer_name": customer.customer_name if customer else "-",
            "customer_phone": customer.phone if customer else None,
            "biz_type": trip.biz_type,
            "item_count": trip.item_count,
            "status": trip.status,
            "remark": trip.remark,
            "create_time": trip.create_time,
        },
        "items": items,
        "readings": readings,
        "summary": {
            "total_settle_weight": round(float(total_settle), 2),
            "total_amount": round(float(total_amount), 2),
            "pending_price": sum(1 for i in items if i["status"] == 0),
            "priced": sum(1 for i in items if i["status"] == 1),
            "completed": sum(1 for i in items if i["status"] == 2),
            "settled": sum(1 for i in items if i["status"] == 3),
            "cancelled": sum(1 for i in items if i["status"] == 4),
        },
    }
