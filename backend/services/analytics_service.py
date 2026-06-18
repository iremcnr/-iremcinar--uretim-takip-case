from __future__ import annotations

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.production import ProductionRecord, ValidationIssue


def _base_query(db: Session, filters: dict):
    q = db.query(ProductionRecord)

    if filters.get("date_from"):
        q = q.filter(ProductionRecord.tarih >= filters["date_from"])
    if filters.get("date_to"):
        q = q.filter(ProductionRecord.tarih <= filters["date_to"])
    if filters.get("shifts"):
        q = q.filter(ProductionRecord.vardiya.in_(filters["shifts"]))
    if filters.get("stations"):
        q = q.filter(ProductionRecord.is_istasyon_adi.in_(filters["stations"]))
    if filters.get("products"):
        q = q.filter(ProductionRecord.stok_adi.in_(filters["products"]))
    if filters.get("oee_min") is not None:
        q = q.filter(ProductionRecord.oee >= filters["oee_min"])
    if filters.get("oee_max") is not None:
        q = q.filter(ProductionRecord.oee <= filters["oee_max"])
    if filters.get("issues_only"):
        q = q.filter(ProductionRecord.validation_status.in_(["rejected", "warning"]))
    return q


def query_records(
    db: Session,
    filters: dict,
    skip: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> dict:
    sort_columns = {
        "record_id": ProductionRecord.record_id,
        "tarih": ProductionRecord.tarih,
        "is_istasyon_adi": ProductionRecord.is_istasyon_adi,
        "stok_adi": ProductionRecord.stok_adi,
        "vardiya": ProductionRecord.vardiya,
        "oee": ProductionRecord.oee,
        "uretilen_miktar": ProductionRecord.uretilen_miktar,
        "hatali_miktar": ProductionRecord.hatali_miktar,
        "validation_status": ProductionRecord.validation_status,
    }

    q = _base_query(db, filters)
    total = q.count()

    if sort_by and sort_by in sort_columns:
        col = sort_columns[sort_by]
        q = q.order_by(col.desc() if sort_order == "desc" else col.asc())
    else:
        q = q.order_by(ProductionRecord.tarih, ProductionRecord.record_id)

    records = q.offset(skip).limit(limit).all()
    return {"total": total, "records": records}


def get_filter_options(db: Session) -> dict:
    stations = [r[0] for r in db.query(ProductionRecord.is_istasyon_adi).distinct().all() if r[0]]
    products = [r[0] for r in db.query(ProductionRecord.stok_adi).distinct().all() if r[0]]
    dates = db.query(func.min(ProductionRecord.tarih), func.max(ProductionRecord.tarih)).first()
    return {
        "stations": sorted(stations),
        "products": sorted(products),
        "date_min": dates[0] if dates else None,
        "date_max": dates[1] if dates else None,
    }


def get_dashboard(db: Session, filters: dict | None = None) -> dict:
    filters = filters or {}
    q = _base_query(db, filters)

    records = q.all()
    if not records:
        return {
            "kpis": {"avg_oee": 0, "total_production": 0, "total_scrap": 0, "total_downtime": 0},
            "oee_trend": [],
            "shift_comparison": [],
            "station_ranking": [],
            "scrap_distribution": [],
        }

    valid_oee = [
        min(r.oee, 100) for r in records if r.oee is not None and r.validation_status != "rejected"
    ]
    total_prod = sum(r.uretilen_miktar or 0 for r in records)
    total_scrap = sum(r.hatali_miktar or 0 for r in records)
    total_downtime = sum(r.durus_suresi or 0 for r in records)

    # Daily OEE trend
    daily: dict[str, list[float]] = {}
    for r in records:
        if r.oee is not None and r.validation_status != "rejected":
            daily.setdefault(r.tarih, []).append(min(r.oee, 100))
    oee_trend = [
        {"date": d, "avg_oee": round(sum(v) / len(v), 2)}
        for d, v in sorted(daily.items())
    ]

    # Shift comparison
    shift_data: dict[int, list[float]] = {}
    for r in records:
        if r.vardiya and r.oee is not None and r.validation_status != "rejected":
            shift_data.setdefault(r.vardiya, []).append(min(r.oee, 100))
    shift_comparison = [
        {"shift": s, "avg_oee": round(sum(v) / len(v), 2), "count": len(v)}
        for s, v in sorted(shift_data.items())
    ]

    # Station ranking
    station_data: dict[str, list[float]] = {}
    for r in records:
        if r.is_istasyon_adi and r.oee is not None and r.validation_status != "rejected":
            station_data.setdefault(r.is_istasyon_adi, []).append(min(r.oee, 100))
    station_ranking = sorted(
        [
            {"station": s, "avg_oee": round(sum(v) / len(v), 2), "count": len(v)}
            for s, v in station_data.items()
        ],
        key=lambda x: x["avg_oee"],
        reverse=True,
    )[:15]

    # Scrap rate distribution by product
    product_scrap: dict[str, dict] = {}
    for r in records:
        if not r.stok_adi:
            continue
        bucket = product_scrap.setdefault(r.stok_adi, {"production": 0, "scrap": 0})
        bucket["production"] += r.uretilen_miktar or 0
        bucket["scrap"] += r.hatali_miktar or 0
    scrap_distribution = sorted(
        [
            {
                "product": p,
                "scrap_rate": round(d["scrap"] / d["production"] * 100, 2) if d["production"] else 0,
                "production": d["production"],
                "scrap": d["scrap"],
            }
            for p, d in product_scrap.items()
            if d["production"] > 0
        ],
        key=lambda x: x["scrap_rate"],
        reverse=True,
    )[:10]

    return {
        "kpis": {
            "avg_oee": round(sum(valid_oee) / len(valid_oee), 2) if valid_oee else 0,
            "total_production": total_prod,
            "total_scrap": total_scrap,
            "total_downtime": round(total_downtime, 2),
        },
        "oee_trend": oee_trend,
        "shift_comparison": shift_comparison,
        "station_ranking": station_ranking,
        "scrap_distribution": scrap_distribution,
    }


def get_validation_report(db: Session, batch_id: str | None = None) -> dict:
    q = db.query(ValidationIssue)
    if batch_id:
        q = q.filter(ValidationIssue.import_batch_id == batch_id)

    issues = q.order_by(ValidationIssue.record_id).all()
    breakdown: dict[str, int] = {}
    for i in issues:
        breakdown[i.error_type] = breakdown.get(i.error_type, 0) + 1

    return {
        "total_issues": len(issues),
        "breakdown": breakdown,
        "issues": issues,
    }
