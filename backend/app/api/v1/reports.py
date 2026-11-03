"""报表接口。"""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.response import ok
from app.core.database import get_db
from app.core.deps import require_perm
from app.core.principal import Principal
from app.repositories import stats_repo

router = APIRouter(prefix="/reports", tags=["报表"])


@router.get("/daily")
def daily(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("report:view")),
):
    end = end or date.today()
    start = start or (end - timedelta(days=6))
    rows = stats_repo.daily_report(db, principal.tenant_id, start, end)
    summary = {
        "net_weight": round(sum(r["net_weight"] for r in rows), 2),
        "deduct_weight": round(sum(r["deduct_weight"] for r in rows), 2),
        "settle_weight": round(sum(r["settle_weight"] for r in rows), 2),
        "item_count": sum(r["item_count"] for r in rows),
    }
    return ok({"start": start, "end": end, "rows": rows, "summary": summary})
