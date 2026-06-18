import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from schemas.production import RecordOut, RecordUpdate, ValidationIssueOut
from services.analytics_service import get_validation_report
from services.import_service import import_csv, preview_csv, update_record
from models.production import AuditLog

router = APIRouter(prefix="/import", tags=["Import"])


@router.post("/preview")
async def preview(file: UploadFile = File(...)):
    content = await file.read()
    return preview_csv(content)


@router.post("")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    result = import_csv(db, content, file.filename or "upload.csv")
    return result


@router.get("/batches")
def list_batches(db: Session = Depends(get_db)):
    from models.production import ImportBatch

    batches = db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).all()
    return [
        {
            "id": b.id,
            "filename": b.filename,
            "total_rows": b.total_rows,
            "imported_rows": b.imported_rows,
            "rejected_rows": b.rejected_rows,
            "warning_rows": b.warning_rows,
            "created_at": b.created_at.isoformat(),
        }
        for b in batches
    ]


@router.get("/validation/export")
def export_validation_report(batch_id: Optional[str] = None, db: Session = Depends(get_db)):
    from fastapi.responses import StreamingResponse

    report = get_validation_report(db, batch_id)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["record_id", "error_type", "fields", "message", "severity", "suggested_action"],
    )
    writer.writeheader()
    for issue in report["issues"]:
        writer.writerow(
            {
                "record_id": issue.record_id,
                "error_type": issue.error_type,
                "fields": issue.fields,
                "message": issue.message,
                "severity": issue.severity,
                "suggested_action": issue.suggested_action,
            }
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="validation_report.csv"'},
    )


@router.get("/validation", response_model=dict)
def validation_report(batch_id: Optional[str] = None, db: Session = Depends(get_db)):
    report = get_validation_report(db, batch_id)
    return {
        "total_issues": report["total_issues"],
        "breakdown": report["breakdown"],
        "issues": [ValidationIssueOut.model_validate(i) for i in report["issues"]],
    }


@router.patch("/records/{record_id}", response_model=RecordOut)
def patch_record(record_id: int, body: RecordUpdate, db: Session = Depends(get_db)):
    updates = body.model_dump(exclude={"action"}, exclude_none=True)
    try:
        record = update_record(db, record_id, updates, action=body.action)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return record


@router.get("/records/{record_id}/audit")
def record_audit(record_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.record_id == record_id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )
    return [
        {
            "id": l.id,
            "field_name": l.field_name,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "action": l.action,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
