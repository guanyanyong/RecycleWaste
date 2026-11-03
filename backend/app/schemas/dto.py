"""请求/响应模型。"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------- 认证 ----------
class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=4, max_length=64)


class UserInfo(BaseModel):
    user_id: int
    username: str
    real_name: str
    tenant_id: int
    tenant_name: str
    roles: list[str]
    permissions: list[str]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


# ---------- 过磅 ----------
class TripCreate(BaseModel):
    station_id: int
    biz_type: int = Field(default=1, ge=1, le=2)
    customer_id: int | None = None
    customer_name: str | None = Field(default=None, max_length=100)
    customer_phone: str | None = Field(default=None, max_length=20)
    plate_no: str | None = Field(default=None, max_length=20)
    driver_name: str | None = Field(default=None, max_length=50)
    remark: str | None = Field(default=None, max_length=500)


class ItemAdd(BaseModel):
    material_id: int
    weight: Decimal | None = Field(default=None, gt=0, le=Decimal("200"))
    weigh_mode: int = Field(default=1, ge=1, le=2)
    reuse_reading_id: int | None = None

    @field_validator("weight")
    @classmethod
    def _round(cls, v: Decimal | None) -> Decimal | None:
        return v.quantize(Decimal("0.01")) if v is not None else None


class PriceRequest(BaseModel):
    unit_price: Decimal = Field(gt=0, le=Decimal("1000000"))
    price_type: int = Field(default=1, ge=1, le=2)
    price_source: str | None = Field(default=None, max_length=50)
    deduct_type: int = Field(default=1, ge=1, le=3)  # 1比例扣重 2固定扣重 3比例扣款
    deduct_ratio: Decimal | None = Field(default=None, ge=0, le=1)
    deduct_fixed: Decimal | None = Field(default=None, ge=0, le=Decimal("50"))
    calc_base: int = Field(default=2, ge=1, le=2)  # 1毛重 2净重


class CompleteRequest(BaseModel):
    end_weight: Decimal | None = Field(default=None, gt=0, le=Decimal("200"))


class SettleCreate(BaseModel):
    item_ids: list[int] = Field(min_length=1)
    settle_mode: int = Field(default=3, ge=1, le=3)
    remark: str | None = Field(default=None, max_length=500)


class PayRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    remark: str | None = Field(default=None, max_length=200)


# ---------- 基础数据 ----------
class MaterialUpsert(BaseModel):
    material_code: str = Field(min_length=1, max_length=50)
    material_name: str = Field(min_length=1, max_length=100)
    category_id: int | None = None
    unit: str = Field(default="吨", max_length=10)
    default_price: Decimal | None = Field(default=None, ge=0)
    price_type: int = Field(default=1, ge=1, le=2)
    sort_no: int = 0
    status: int = Field(default=1, ge=0, le=1)
    remark: str | None = Field(default=None, max_length=200)


class CategoryUpsert(BaseModel):
    category_code: str = Field(min_length=1, max_length=50)
    category_name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None


class StationUpsert(BaseModel):
    station_name: str = Field(min_length=1, max_length=100)
    station_code: str = Field(min_length=1, max_length=50)
    address: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=50)
    contact_phone: str | None = Field(default=None, max_length=20)
    status: int = Field(default=1, ge=0, le=1)


class CustomerUpsert(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    customer_type: int = Field(default=1, ge=1, le=2)
    address: str | None = Field(default=None, max_length=200)
    remark: str | None = Field(default=None, max_length=200)


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=64)
    real_name: str = Field(min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    role_codes: list[str] = Field(default_factory=list)
    station_scope: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    real_name: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    status: int | None = Field(default=None, ge=0, le=1)
    role_codes: list[str] | None = None
    station_scope: list[int] | None = None
    password: str | None = Field(default=None, min_length=6, max_length=64)


class DeductRuleUpsert(BaseModel):
    rule_name: str = Field(min_length=1, max_length=50)
    material_id: int | None = None
    deduct_type: int = Field(ge=1, le=3)
    ratio: Decimal | None = Field(default=None, ge=0, le=1)
    fixed_value: Decimal | None = Field(default=None, ge=0)
    calc_base: int = Field(default=2, ge=1, le=2)
    priority: int = 0
    status: int = Field(default=1, ge=0, le=1)


class ReportQuery(BaseModel):
    start: date
    end: date
