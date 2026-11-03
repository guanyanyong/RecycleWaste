"""生成「多车并行」在场工单演示数据（5 张不同阶段的工单）。

用于演示过磅工作台同时处理 3~5 辆车的真实场景：
  1) 刚开单、还没有批次（可演示作废空工单）
  2) 已录毛重、等待质检核价
  3) 一件已核价待皮重 + 一件待核价
  4) 两件均已称重完成，等待结算
  5) 单次过磅完成，等待结算

仅重建 status in (0,1) 的在场工单，不动历史已结算数据与基础数据。
用法：python scripts/seed_active_tickets.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models.entities import Customer, Material, WeighItem, WeighReading, WeighTrip

TENANT = 1
OPERATOR = 1
Q2 = Decimal("0.01")


def q2(v) -> Decimal:
    return Decimal(v).quantize(Q2, rounding=ROUND_HALF_UP)


def main() -> None:
    db = SessionLocal()
    try:
        # 清理旧的在场工单
        active_ids = list(
            db.scalars(
                select(WeighTrip.trip_id).where(
                    WeighTrip.tenant_id == TENANT, WeighTrip.status.in_((0, 1))
                )
            )
        )
        if active_ids:
            db.execute(delete(WeighItem).where(WeighItem.trip_id.in_(active_ids)))
            db.execute(delete(WeighReading).where(WeighReading.trip_id.in_(active_ids)))
            db.execute(delete(WeighTrip).where(WeighTrip.trip_id.in_(active_ids)))
            db.flush()

        customers = {
            c.customer_name: c
            for c in db.scalars(select(Customer).where(Customer.tenant_id == TENANT))
        }
        materials = {
            m.material_name: m
            for m in db.scalars(
                select(Material).where(Material.tenant_id == TENANT, Material.status == 1)
            )
        }

        now = datetime.now()
        seq = 0

        def new_trip(plate: str, customer_name: str, driver: str, biz_type: int,
                     minutes_ago: int) -> WeighTrip:
            nonlocal seq
            seq += 1
            created = now - timedelta(minutes=minutes_ago)
            customer = customers[customer_name]
            trip = WeighTrip(
                tenant_id=TENANT,
                station_id=1,
                trip_no=f"{'IN' if biz_type == 1 else 'OUT'}{created:%Y%m%d%H%M%S}{seq:02d}",
                plate_no=plate,
                driver_name=driver,
                customer_id=customer.customer_id,
                biz_type=biz_type,
                item_count=0,
                status=0,
            )
            trip.create_time = created
            trip.update_time = created
            db.add(trip)
            db.flush()
            return trip

        def add_item(trip: WeighTrip, material_name: str, gross: float, tare: float | None,
                     weigh_mode: int, price: float | None, ratio: float | None,
                     status: int, minutes_ago: int) -> WeighItem:
            material = materials[material_name]
            created = now - timedelta(minutes=minutes_ago)
            item_seq = trip.item_count + 1

            r1 = WeighReading(
                tenant_id=TENANT, trip_id=trip.trip_id, seq=item_seq * 2 - 1,
                weight=q2(gross), reading_time=created, operator_id=OPERATOR,
            )
            r1.create_time = created
            db.add(r1)
            db.flush()

            net = q2(gross - tare) if tare is not None else (q2(gross) if weigh_mode == 2 else None)
            deduct = Decimal("0.00")
            settle_weight = None
            snapshot = None
            if price is not None:
                snapshot = {"deduct_type": 1, "ratio": ratio, "calc_base": 2}
                if net is not None:
                    deduct = q2(net * Decimal(str(ratio)))
                    settle_weight = q2(net - deduct)

            end_reading_id = None
            if tare is not None:
                r2 = WeighReading(
                    tenant_id=TENANT, trip_id=trip.trip_id, seq=item_seq * 2,
                    weight=q2(tare), reading_time=created + timedelta(minutes=8),
                    operator_id=OPERATOR,
                )
                r2.create_time = created + timedelta(minutes=8)
                db.add(r2)
                db.flush()
                end_reading_id = r2.reading_id

            item = WeighItem(
                tenant_id=TENANT,
                trip_id=trip.trip_id,
                seq=item_seq,
                ticket_no=f"{trip.trip_no}-{item_seq:02d}",
                material_id=material.material_id,
                customer_id=trip.customer_id,
                biz_type=trip.biz_type,
                weigh_mode=weigh_mode,
                start_reading_id=r1.reading_id,
                end_reading_id=end_reading_id,
                start_weight=q2(gross),
                end_weight=q2(tare) if tare is not None else None,
                net_weight=net,
                deduct_weight=deduct,
                deduct_detail={"deduct_type": 1, "ratio": ratio, "calc_base": 2} if price else None,
                settle_weight=settle_weight,
                unit_price=Decimal(str(price)).quantize(Decimal("0.0001")) if price else None,
                price_type=1 if price else None,
                deduct_rule_snapshot=snapshot,
                pricing_user_id=OPERATOR if price else None,
                pricing_time=created + timedelta(minutes=3) if price else None,
                status=status,
            )
            item.create_time = created
            item.update_time = created + timedelta(minutes=9)
            db.add(item)
            db.flush()

            trip.item_count = item_seq
            return item

        # 01 刚开单，尚无批次（可演示作废空工单）
        new_trip("粤B12345", "张建国", "张师傅", 1, minutes_ago=9)

        # 02 已录毛重，等待核价
        t2 = new_trip("粤B67890", "李秀兰", "李师傅", 1, minutes_ago=26)
        add_item(t2, "重废", 12.60, None, 1, None, None, 0, minutes_ago=24)
        t2.status = 0

        # 03 一件已核价待皮重 + 一件待核价
        t3 = new_trip("粤B3F218", "顺发废品回收站", "王师傅", 1, minutes_ago=48)
        add_item(t3, "光亮铜", 6.80, None, 1, 62500, 0.01, 1, minutes_ago=46)
        add_item(t3, "废电缆铜", 3.45, None, 2, 38000, 0.02, 0, minutes_ago=31)
        t3.status = 0

        # 04 两件全部称重完成，等待结算
        t4 = new_trip("粤B9K662", "王海涛", "刘师傅", 1, minutes_ago=96)
        add_item(t4, "废铁", 9.60, 3.20, 1, 2100, 0.02, 2, minutes_ago=94)
        add_item(t4, "轻薄料", 4.80, 2.05, 1, 1350, 0.03, 2, minutes_ago=63)
        t4.status = 1

        # 05 单次过磅完成，等待结算
        t5 = new_trip("粤B5Q771", "张建国", "赵师傅", 2, minutes_ago=135)
        add_item(t5, "混合铜", 5.20, None, 2, 41000, 0.02, 2, minutes_ago=132)
        t5.status = 1

        db.commit()

        rows = db.scalars(
            select(WeighTrip).where(WeighTrip.tenant_id == TENANT, WeighTrip.status.in_((0, 1)))
            .order_by(WeighTrip.trip_id)
        ).all()
        print(f"在场工单已生成：{len(rows)} 张")
        for t in rows:
            print(f"  {t.trip_no}  车牌 {t.plate_no}  批次 {t.item_count}  状态 {t.status}")
        print("历史行程数：", db.scalar(select(func.count()).select_from(WeighTrip)))
    finally:
        db.close()


if __name__ == "__main__":
    main()
