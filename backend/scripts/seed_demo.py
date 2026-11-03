"""生成演示数据：最近 7 天的行程/读数/批次/结算，便于查看看板与报表效果。

仅清理并重建 tenant_id=1 的业务数据（不会动基础数据/账号）。
用法：python scripts/seed_demo.py
"""
from __future__ import annotations

import random
import sys
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.entities import (
    Customer,
    Material,
    SettleDetail,
    SettleRecord,
    WeighItem,
    WeighReading,
    WeighTrip,
)

TENANT = 1
random.seed(20261103)


def q2(v) -> Decimal:
    return Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> None:
    db = SessionLocal()
    try:
        # 清理业务数据与自动化测试客户
        db.execute(delete(SettleDetail).where(SettleDetail.tenant_id == TENANT))
        db.execute(delete(SettleRecord).where(SettleRecord.tenant_id == TENANT))
        db.execute(delete(WeighItem).where(WeighItem.tenant_id == TENANT))
        db.execute(delete(WeighReading).where(WeighReading.tenant_id == TENANT))
        db.execute(delete(WeighTrip).where(WeighTrip.tenant_id == TENANT))
        db.execute(
            delete(Customer).where(
                Customer.tenant_id == TENANT,
                Customer.customer_code.notin_(["C0001", "C0002", "C0003", "C0004"]),
            )
        )
        db.flush()

        customers = list(
            db.scalars(select(Customer).where(Customer.tenant_id == TENANT).order_by(Customer.customer_id))
        )
        materials = list(
            db.scalars(
                select(Material).where(Material.tenant_id == TENANT, Material.status == 1)
                .order_by(Material.sort_no)
            )
        )
        plates = ["粤B12345", "粤B67890", "粤B3F218", "粤B9K662", "粤B5Q771"]

        trip_seq = 0
        settle_seq = 0
        today = date.today()

        for day_offset in range(6, -1, -1):
            day = today - timedelta(days=day_offset)
            trip_total = 3 if day_offset in (6, 3, 0) else random.randint(1, 2)
            for i in range(trip_total):
                trip_seq += 1
                customer = customers[(trip_seq + i) % len(customers)]
                base_dt = datetime.combine(day, time(8, 30)) + timedelta(minutes=47 * i + 12)
                plate = plates[trip_seq % len(plates)]
                trip_no = f"IN{base_dt:%Y%m%d%H%M%S}{trip_seq % 100:02d}"
                trip = WeighTrip(
                    tenant_id=TENANT,
                    station_id=1,
                    trip_no=trip_no,
                    plate_no=plate,
                    driver_name=random.choice(["张师傅", "李师傅", "王师傅", "刘师傅"]),
                    customer_id=customer.customer_id,
                    biz_type=1,
                    item_count=0,
                    status=0,
                    remark=None,
                )
                # 通过显式赋值覆盖 server_default
                trip.create_time = base_dt
                trip.update_time = base_dt
                db.add(trip)
                db.flush()

                item_total = 2 if trip_seq % 3 == 0 else 1
                reading_seq = 0
                items = []
                for j in range(item_total):
                    material = materials[(trip_seq * 2 + j) % len(materials)]
                    gross = q2(random.uniform(3.2, 14.5))
                    tare = q2(random.uniform(0.8, min(3.0, float(gross) - 0.6)))

                    reading_seq += 1
                    r1 = WeighReading(
                        tenant_id=TENANT, trip_id=trip.trip_id, seq=reading_seq,
                        weight=gross, reading_time=base_dt + timedelta(minutes=j * 18),
                        operator_id=1,
                    )
                    r1.create_time = base_dt + timedelta(minutes=j * 18)
                    db.add(r1)
                    db.flush()

                    mode = 1
                    reading_seq += 1
                    r2 = WeighReading(
                        tenant_id=TENANT, trip_id=trip.trip_id, seq=reading_seq,
                        weight=tare, reading_time=base_dt + timedelta(minutes=j * 18 + 14),
                        operator_id=1,
                    )
                    r2.create_time = base_dt + timedelta(minutes=j * 18 + 14)
                    db.add(r2)
                    db.flush()

                    net = q2(gross - tare)
                    ratio = Decimal(random.choice(["0.01", "0.02", "0.03", "0.025"]))
                    deduct = q2(net * ratio)
                    settle_weight = q2(net - deduct)
                    price = Decimal(material.default_price or 2000).quantize(Decimal("0.0001"))

                    item = WeighItem(
                        tenant_id=TENANT, trip_id=trip.trip_id, seq=j + 1,
                        ticket_no=f"{trip_no}-{j + 1:02d}",
                        material_id=material.material_id,
                        customer_id=customer.customer_id, biz_type=1, weigh_mode=mode,
                        start_reading_id=r1.reading_id, end_reading_id=r2.reading_id,
                        start_weight=gross, end_weight=tare, net_weight=net,
                        deduct_weight=deduct,
                        deduct_detail={"deduct_type": 1, "ratio": float(ratio), "calc_base": 2},
                        settle_weight=settle_weight,
                        unit_price=price, price_type=1,
                        deduct_rule_snapshot={"deduct_type": 1, "ratio": float(ratio), "calc_base": 2},
                        pricing_user_id=1,
                        pricing_time=base_dt + timedelta(minutes=j * 18 + 5),
                        status=2,
                    )
                    item.create_time = base_dt + timedelta(minutes=j * 18)
                    item.update_time = base_dt + timedelta(minutes=j * 18 + 20)
                    db.add(item)
                    db.flush()
                    items.append(item)

                trip.item_count = item_total

                # 状态分布：历史全部已结算，今天保留部分待处理
                settled = day_offset >= 2 or (day_offset == 1 and trip_seq % 2 == 0)
                if settled:
                    settle_seq += 1
                    settle_no = f"ST{base_dt:%Y%m%d%H%M%S}{settle_seq % 100:02d}"
                    total_w = sum((it.settle_weight for it in items), Decimal("0"))
                    total_a = sum((q2(it.settle_weight * it.unit_price) for it in items), Decimal("0"))
                    rec = SettleRecord(
                        tenant_id=TENANT, station_id=1, settle_no=settle_no, settle_mode=3,
                        trip_id=trip.trip_id, customer_id=customer.customer_id, biz_type=1,
                        settle_date=day, total_settle_weight=total_w, total_amount=total_a,
                        paid_amount=total_a, pay_status=2,
                        material_summary=[
                            {"material_id": it.material_id, "weight": float(it.settle_weight),
                             "amount": float(q2(it.settle_weight * it.unit_price))}
                            for it in items
                        ],
                    )
                    rec.create_time = base_dt + timedelta(hours=2)
                    rec.update_time = base_dt + timedelta(hours=2)
                    db.add(rec)
                    db.flush()
                    for it in items:
                        detail = SettleDetail(
                            tenant_id=TENANT, settle_id=rec.settle_id, weigh_item_id=it.item_id,
                            trip_id=it.trip_id, ticket_no=it.ticket_no, material_id=it.material_id,
                            net_weight=it.net_weight, deduct_weight=it.deduct_weight,
                            settle_weight=it.settle_weight, unit_price=it.unit_price,
                            price_type=1, amount=q2(it.settle_weight * it.unit_price),
                            deduct_amount=Decimal("0.00"), final_amount=q2(it.settle_weight * it.unit_price),
                        )
                        detail.create_time = base_dt + timedelta(hours=2)
                        db.add(detail)
                        it.settle_id = rec.settle_id
                        it.status = 3
                    trip.status = 2
                else:
                    # 今天：部分称重完成待结算，一条停留在新建/核价
                    if trip_seq % 4 == 0:
                        items[0].status = 0
                        items[0].net_weight = None
                        items[0].settle_weight = None
                        items[0].unit_price = None
                        items[0].pricing_time = None
                        items[0].pricing_user_id = None
                        items[0].end_reading_id = None
                        items[0].end_weight = None
                        items[0].deduct_weight = Decimal("0.00")
                        items[0].deduct_detail = None
                        items[0].deduct_rule_snapshot = None
                        trip.status = 0
                    elif trip_seq % 4 == 1:
                        items[0].status = 1
                        items[0].net_weight = None
                        items[0].settle_weight = None
                        items[0].end_reading_id = None
                        items[0].end_weight = None
                        items[0].deduct_weight = Decimal("0.00")
                        items[0].deduct_detail = None
                        trip.status = 0
                    else:
                        trip.status = 1

                db.flush()

        db.commit()
        print("演示数据生成完成：")
        print("  行程", db.scalar(select(func.count()).select_from(WeighTrip)))
        print("  批次", db.scalar(select(func.count()).select_from(WeighItem)))
        print("  结算单", db.scalar(select(func.count()).select_from(SettleRecord)))
    finally:
        db.close()


if __name__ == "__main__":
    main()
