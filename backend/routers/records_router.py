import csv
import io

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.production import RecordOut
from services.analytics_service import get_dashboard, get_filter_options, query_records

router = APIRouter(tags=["Records & Analytics"])


@router.get("/records")
def list_records(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    shifts: Optional[str] = Query(None, description="Comma-separated shift numbers"),
    stations: Optional[str] = Query(None, description="Comma-separated station names"),
    products: Optional[str] = Query(None, description="Comma-separated product names"),
    oee_min: Optional[float] = None,
    oee_max: Optional[float] = None,
    issues_only: bool = False,
    skip: int = 0,
    limit: int = 10,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    db: Session = Depends(get_db),
):
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "shifts": [int(s) for s in shifts.split(",")] if shifts else None,
        "stations": stations.split(",") if stations else None,
        "products": products.split(",") if products else None,
        "oee_min": oee_min,
        "oee_max": oee_max,
        "issues_only": issues_only,
    }
    result = query_records(db, filters, skip, limit, sort_by, sort_order)
    return {
        "total": result["total"],
        "records": [RecordOut.model_validate(r) for r in result["records"]],
    }


@router.get("/records/export")
def export_records(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    shifts: Optional[str] = None,
    stations: Optional[str] = None,
    products: Optional[str] = None,
    oee_min: Optional[float] = None,
    oee_max: Optional[float] = None,
    issues_only: bool = False,
    db: Session = Depends(get_db),
):
    from fastapi.responses import StreamingResponse

    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "shifts": [int(s) for s in shifts.split(",")] if shifts else None,
        "stations": stations.split(",") if stations else None,
        "products": products.split(",") if products else None,
        "oee_min": oee_min,
        "oee_max": oee_max,
        "issues_only": issues_only,
    }
    result = query_records(db, filters, skip=0, limit=100000)
    output = io.StringIO()
    fieldnames = [
        "record_id", "tarih", "is_emri_no", "is_istasyon_adi", "stok_adi", "vardiya",
        "availability", "performance", "quality", "oee", "uretilen_miktar",
        "hatali_miktar", "validation_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in result["records"]:
        writer.writerow({f: getattr(r, f) for f in fieldnames})

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=filtered_records.csv"},
    )


@router.get("/filters")
def filters(db: Session = Depends(get_db)):
    return get_filter_options(db)


@router.get("/dashboard")
def dashboard(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    shifts: Optional[str] = None,
    stations: Optional[str] = None,
    products: Optional[str] = None,
    db: Session = Depends(get_db),
):
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "shifts": [int(s) for s in shifts.split(",")] if shifts else None,
        "stations": stations.split(",") if stations else None,
        "products": products.split(",") if products else None,
    }
    return get_dashboard(db, filters)
