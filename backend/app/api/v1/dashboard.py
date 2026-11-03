"""看板接口。"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.response import ok
from app.core.database import get_db
from app.core.deps import get_principal, require_perm
from app.core.principal import Principal
from app.repositories import stats_repo, weigh_repo

router = APIRouter(prefix="/dashboard", tags=["看板"])


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("report:view")),
):
    return ok(stats_repo.overview(db, principal.tenant_id, date.today()))


@router.get("/trend")
def trend(
    days: int = Query(default=7, ge=3, le=30),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("report:view")),
):
    return ok(stats_repo.trend(db, principal.tenant_id, days))


@router.get("/material-distribution")
def material_distribution(
    days: int = Query(default=30, ge=1, le=180),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("report:view")),
):
    return ok(stats_repo.material_distribution(db, principal.tenant_id, days))


@router.get("/station-distribution")
def station_distribution(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("report:view")),
):
    return ok(stats_repo.station_distribution(db, principal.tenant_id))


@router.get("/recent-trips")
def recent_trips(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_perm("weigh:view")),
):
    return ok(weigh_repo.list_trips(db, principal.tenant_id, limit=8))
