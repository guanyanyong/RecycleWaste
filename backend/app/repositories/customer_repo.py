"""客户 / 车辆数据访问。"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Customer, Vehicle


def search_customers(db: Session, tenant_id: int, keyword: str | None = None,
                     limit: int = 20) -> list[Customer]:
    stmt = select(Customer).where(Customer.tenant_id == tenant_id, Customer.status == 1)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(Customer.customer_name.like(like), Customer.phone.like(like),
                Customer.customer_code.like(like))
        )
    return list(db.scalars(stmt.order_by(Customer.customer_id.desc()).limit(limit)))


def list_customers(db: Session, tenant_id: int, keyword: str | None = None) -> list[Customer]:
    stmt = select(Customer).where(Customer.tenant_id == tenant_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(Customer.customer_name.like(like), Customer.phone.like(like),
                Customer.customer_code.like(like))
        )
    return list(db.scalars(stmt.order_by(Customer.customer_id.desc())))


def get_customer(db: Session, tenant_id: int, customer_id: int) -> Customer | None:
    return db.scalar(
        select(Customer).where(Customer.tenant_id == tenant_id, Customer.customer_id == customer_id)
    )


def find_by_phone(db: Session, tenant_id: int, phone: str) -> Customer | None:
    return db.scalar(
        select(Customer).where(Customer.tenant_id == tenant_id, Customer.phone == phone).limit(1)
    )


def count_customers(db: Session, tenant_id: int) -> int:
    return int(
        db.scalar(select(func.count()).select_from(Customer).where(Customer.tenant_id == tenant_id)) or 0
    )


def next_customer_code(db: Session, tenant_id: int) -> str:
    n = count_customers(db, tenant_id) + 1
    return f"C{n:04d}"


def list_vehicles(db: Session, tenant_id: int) -> list[Vehicle]:
    return list(
        db.scalars(select(Vehicle).where(Vehicle.tenant_id == tenant_id).order_by(Vehicle.vehicle_id))
    )


def find_vehicle_by_plate(db: Session, tenant_id: int, plate_no: str) -> Vehicle | None:
    return db.scalar(
        select(Vehicle).where(Vehicle.tenant_id == tenant_id, Vehicle.plate_no == plate_no)
    )
