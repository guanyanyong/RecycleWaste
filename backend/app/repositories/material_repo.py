"""物料 / 分类 / 扣杂规则数据访问。"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import DeductRule, Material, MaterialCategory, TenantCategory


def visible_categories(db: Session, tenant_id: int) -> list[dict]:
    """按「系统预置 + 租户自定义」懒加载规则取可见分类。"""
    tc = (
        select(TenantCategory)
        .where(TenantCategory.tenant_id == tenant_id)
        .subquery()
    )
    stmt = (
        select(MaterialCategory, tc.c.is_enabled, tc.c.sort_no)
        .outerjoin(tc, tc.c.category_id == MaterialCategory.category_id)
        .where(
            MaterialCategory.status == 1,
            or_(
                (MaterialCategory.tenant_id.is_(None))
                & (or_(tc.c.is_enabled.is_(None), tc.c.is_enabled == 1)),
                MaterialCategory.tenant_id == tenant_id,
            ),
        )
    )
    rows = db.execute(stmt).all()
    result = []
    for cat, _, tenant_sort in rows:
        result.append(
            {
                "category_id": cat.category_id,
                "tenant_id": cat.tenant_id,
                "parent_id": cat.parent_id,
                "category_code": cat.category_code,
                "category_name": cat.category_name,
                "level": cat.level,
                "sort_no": tenant_sort if tenant_sort is not None else cat.sort_no,
                "is_builtin": cat.is_builtin,
                "status": cat.status,
            }
        )
    result.sort(key=lambda x: (x["level"], x["sort_no"], x["category_id"]))
    return result


def get_category(db: Session, category_id: int) -> MaterialCategory | None:
    return db.get(MaterialCategory, category_id)


def list_materials(db: Session, tenant_id: int, keyword: str | None = None,
                   category_id: int | None = None, status: int | None = None) -> list[dict]:
    stmt = (
        select(Material, MaterialCategory.category_name)
        .outerjoin(MaterialCategory, MaterialCategory.category_id == Material.category_id)
        .where(Material.tenant_id == tenant_id)
    )
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Material.material_name.like(like), Material.material_code.like(like)))
    if category_id:
        # 选中父分类时包含其子分类
        child_ids = list(
            db.scalars(select(MaterialCategory.category_id).where(MaterialCategory.parent_id == category_id))
        )
        ids = [category_id, *child_ids]
        stmt = stmt.where(Material.category_id.in_(ids))
    if status is not None:
        stmt = stmt.where(Material.status == status)
    rows = db.execute(stmt.order_by(Material.sort_no, Material.material_id)).all()
    return [
        {
            "material_id": m.material_id,
            "tenant_id": m.tenant_id,
            "category_id": m.category_id,
            "category_name": cname,
            "material_code": m.material_code,
            "material_name": m.material_name,
            "unit": m.unit,
            "default_price": m.default_price,
            "price_type": m.price_type,
            "status": m.status,
            "sort_no": m.sort_no,
            "remark": m.remark,
        }
        for m, cname in rows
    ]


def get_material(db: Session, tenant_id: int, material_id: int) -> Material | None:
    return db.scalar(
        select(Material).where(Material.tenant_id == tenant_id, Material.material_id == material_id)
    )


def material_name(db: Session, material_id: int) -> str:
    name = db.scalar(select(Material.material_name).where(Material.material_id == material_id))
    return name or "-"


def count_material_code(db: Session, tenant_id: int, code: str, exclude_id: int | None = None) -> int:
    stmt = select(func.count()).select_from(Material).where(
        Material.tenant_id == tenant_id, Material.material_code == code
    )
    if exclude_id:
        stmt = stmt.where(Material.material_id != exclude_id)
    return int(db.scalar(stmt) or 0)


def list_deduct_rules(db: Session, tenant_id: int) -> list[dict]:
    rows = db.execute(
        select(DeductRule, Material.material_name)
        .outerjoin(Material, Material.material_id == DeductRule.material_id)
        .where(DeductRule.tenant_id == tenant_id)
        .order_by(DeductRule.priority, DeductRule.rule_id)
    ).all()
    return [
        {
            "rule_id": r.rule_id,
            "material_id": r.material_id,
            "material_name": mname,
            "rule_name": r.rule_name,
            "deduct_type": r.deduct_type,
            "ratio": r.ratio,
            "fixed_value": r.fixed_value,
            "calc_base": r.calc_base,
            "priority": r.priority,
            "status": r.status,
        }
        for r, mname in rows
    ]


def best_rule(db: Session, tenant_id: int, material_id: int) -> DeductRule | None:
    """取物料专属优先，其次租户通用；同优先级取优先级高者。"""
    return db.scalar(
        select(DeductRule)
        .where(
            DeductRule.tenant_id == tenant_id,
            DeductRule.status == 1,
            or_(DeductRule.material_id == material_id, DeductRule.material_id.is_(None)),
        )
        .order_by(
            DeductRule.material_id.is_(None),  # 非空(物料专属)排前面
            DeductRule.priority.desc(),
            DeductRule.rule_id,
        )
        .limit(1)
    )
