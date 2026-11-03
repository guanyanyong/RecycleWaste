"""ORM 实体：与数据库设计一一对应（含业务扩展表 biz_customer / biz_vehicle）。"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "sys_tenant"

    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_name: Mapped[str] = mapped_column(String(100))
    tenant_type: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    expire_time: Mapped[datetime | None] = mapped_column(DateTime)
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    remark: Mapped[str | None] = mapped_column(String(500))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Station(Base):
    __tablename__ = "sys_station"

    station_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    station_name: Mapped[str] = mapped_column(String(100))
    station_code: Mapped[str] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(200))
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    real_name: Mapped[str | None] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserTenant(Base):
    __tablename__ = "sys_user_tenant"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    station_scope: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Role(Base):
    __tablename__ = "sys_role"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role_code: Mapped[str] = mapped_column(String(50))
    role_name: Mapped[str] = mapped_column(String(50))
    is_builtin: Mapped[int] = mapped_column(SmallInteger, default=0)
    remark: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserTenantRole(Base):
    __tablename__ = "sys_user_tenant_role"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Permission(Base):
    __tablename__ = "sys_permission"

    perm_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    perm_name: Mapped[str] = mapped_column(String(50))
    perm_group: Mapped[str] = mapped_column(String(50), index=True)
    sort_no: Mapped[int] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(String(200))


class RolePermission(Base):
    __tablename__ = "sys_role_permission"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    perm_id: Mapped[str] = mapped_column(String(50), primary_key=True)


class Device(Base):
    __tablename__ = "sys_device"

    device_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    station_id: Mapped[int] = mapped_column(BigInteger)
    device_type: Mapped[int] = mapped_column(SmallInteger)
    device_name: Mapped[str | None] = mapped_column(String(50))
    device_sn: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MaterialCategory(Base):
    __tablename__ = "material_category"

    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    parent_id: Mapped[int | None] = mapped_column(BigInteger)
    category_code: Mapped[str] = mapped_column(String(50))
    category_name: Mapped[str] = mapped_column(String(100))
    level: Mapped[int] = mapped_column(SmallInteger, default=1)
    sort_no: Mapped[int] = mapped_column(Integer, default=0)
    is_builtin: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    remark: Mapped[str | None] = mapped_column(String(200))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TenantCategory(Base):
    __tablename__ = "tenant_category"

    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_enabled: Mapped[int] = mapped_column(SmallInteger, default=1)
    sort_no: Mapped[int | None] = mapped_column(Integer)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Material(Base):
    __tablename__ = "material"

    material_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    category_id: Mapped[int | None] = mapped_column(BigInteger)
    material_code: Mapped[str] = mapped_column(String(50))
    material_name: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(10), default="吨")
    default_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_type: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    sort_no: Mapped[int] = mapped_column(Integer, default=0)
    remark: Mapped[str | None] = mapped_column(String(200))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WeighTrip(Base):
    __tablename__ = "weigh_trip"

    trip_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    station_id: Mapped[int] = mapped_column(BigInteger)
    trip_no: Mapped[str] = mapped_column(String(50))
    vehicle_id: Mapped[int | None] = mapped_column(BigInteger)
    plate_no: Mapped[str | None] = mapped_column(String(20))
    driver_name: Mapped[str | None] = mapped_column(String(50))
    customer_id: Mapped[int | None] = mapped_column(BigInteger)
    biz_type: Mapped[int] = mapped_column(SmallInteger)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=0)
    remark: Mapped[str | None] = mapped_column(String(500))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WeighReading(Base):
    __tablename__ = "weigh_reading"

    reading_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    trip_id: Mapped[int] = mapped_column(BigInteger)
    seq: Mapped[int] = mapped_column(Integer)
    weight: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reading_time: Mapped[datetime] = mapped_column(DateTime)
    operator_id: Mapped[int | None] = mapped_column("operator", BigInteger)
    device_id: Mapped[int | None] = mapped_column(BigInteger)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WeighItem(Base):
    __tablename__ = "weigh_item"

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    trip_id: Mapped[int] = mapped_column(BigInteger)
    seq: Mapped[int] = mapped_column(Integer)
    ticket_no: Mapped[str] = mapped_column(String(50))
    material_id: Mapped[int] = mapped_column(BigInteger)
    customer_id: Mapped[int | None] = mapped_column(BigInteger)
    biz_type: Mapped[int] = mapped_column(SmallInteger)
    weigh_mode: Mapped[int] = mapped_column(SmallInteger, default=1)
    start_reading_id: Mapped[int] = mapped_column(BigInteger)
    end_reading_id: Mapped[int | None] = mapped_column(BigInteger)
    start_weight: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    end_weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    net_weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    deduct_weight: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    deduct_detail: Mapped[dict | None] = mapped_column(JSON)
    settle_weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_type: Mapped[int | None] = mapped_column(SmallInteger)
    price_source: Mapped[str | None] = mapped_column(String(50))
    deduct_rule_snapshot: Mapped[dict | None] = mapped_column(JSON)
    pricing_user_id: Mapped[int | None] = mapped_column(BigInteger)
    pricing_time: Mapped[datetime | None] = mapped_column(DateTime)
    settle_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=0)
    remark: Mapped[str | None] = mapped_column(String(500))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DeductRule(Base):
    __tablename__ = "tenant_deduct_rule"

    rule_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    material_id: Mapped[int | None] = mapped_column(BigInteger)
    rule_name: Mapped[str] = mapped_column(String(50))
    deduct_type: Mapped[int] = mapped_column(SmallInteger)
    ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    fixed_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    calc_base: Mapped[int | None] = mapped_column(SmallInteger)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TenantConfig(Base):
    __tablename__ = "tenant_config"

    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    config_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    config_value: Mapped[str | None] = mapped_column(String(500))
    remark: Mapped[str | None] = mapped_column(String(200))
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SettleRecord(Base):
    __tablename__ = "settle_record"

    settle_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    station_id: Mapped[int | None] = mapped_column(BigInteger)
    settle_no: Mapped[str] = mapped_column(String(50))
    settle_mode: Mapped[int] = mapped_column(SmallInteger, default=3)
    trip_id: Mapped[int | None] = mapped_column(BigInteger)
    period_start: Mapped[datetime | None] = mapped_column(DateTime)
    period_end: Mapped[datetime | None] = mapped_column(DateTime)
    customer_id: Mapped[int] = mapped_column(BigInteger)
    biz_type: Mapped[int] = mapped_column(SmallInteger)
    settle_date: Mapped[date] = mapped_column(Date)
    total_settle_weight: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    pay_status: Mapped[int] = mapped_column(SmallInteger, default=0)
    material_summary: Mapped[dict | None] = mapped_column(JSON)
    remark: Mapped[str | None] = mapped_column(String(500))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SettleDetail(Base):
    __tablename__ = "settle_detail"

    detail_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    settle_id: Mapped[int] = mapped_column(BigInteger, index=True)
    weigh_item_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    trip_id: Mapped[int | None] = mapped_column(BigInteger)
    ticket_no: Mapped[str | None] = mapped_column(String(50))
    material_id: Mapped[int] = mapped_column(BigInteger)
    net_weight: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    deduct_weight: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    settle_weight: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    price_type: Mapped[int] = mapped_column(SmallInteger, default=1)
    price_source: Mapped[str | None] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    deduct_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    deduct_reason: Mapped[str | None] = mapped_column(String(200))
    final_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Customer(Base):
    __tablename__ = "biz_customer"

    customer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    customer_code: Mapped[str] = mapped_column(String(50))
    customer_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    id_card: Mapped[str | None] = mapped_column(String(30))
    customer_type: Mapped[int] = mapped_column(SmallInteger, default=1)
    address: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    remark: Mapped[str | None] = mapped_column(String(200))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Vehicle(Base):
    __tablename__ = "biz_vehicle"

    vehicle_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True)
    plate_no: Mapped[str] = mapped_column(String(20))
    vehicle_type: Mapped[str | None] = mapped_column(String(30))
    tare_weight: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    owner_customer_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
