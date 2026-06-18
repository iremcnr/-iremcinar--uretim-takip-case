from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from models.production import AuditLog, ImportBatch, ProductionRecord, ValidationIssue
from services.csv_parser import map_row
from services.validation_service import parse_date, validate_record


def _file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def preview_csv(content: bytes, limit: int = 10) -> dict:
    for encoding in ("utf-8-sig", "cp1254", "latin-1", "iso-8859-9"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = content.decode("utf-8", errors="replace")

    df = pd.read_csv(io.StringIO(text))
    rows = df.head(limit).fillna("").astype(str).to_dict(orient="records")
    return {
        "columns": list(df.columns),
        "preview_rows": rows,
        "total_rows": len(df),
    }


def import_csv(db: Session, content: bytes, filename: str) -> dict:
    fhash = _file_hash(content)
    existing = db.query(ImportBatch).filter(ImportBatch.file_hash == fhash).first()
    if existing:
        return {
            "duplicate": True,
            "message": "Bu dosya daha önce yüklendi.",
            "batch_id": existing.id,
            "summary": {
                "total_rows": existing.total_rows,
                "imported_rows": existing.imported_rows,
                "rejected_rows": existing.rejected_rows,
                "warning_rows": existing.warning_rows,
            },
        }

    for encoding in ("utf-8-sig", "cp1254", "latin-1", "iso-8859-9"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = content.decode("utf-8", errors="replace")

    df = pd.read_csv(io.StringIO(text))
    batch_id = str(uuid.uuid4())
    existing_ids = {r.record_id for r in db.query(ProductionRecord.record_id).all()}

    imported = rejected = warnings = 0
    issue_breakdown: dict[str, int] = {}

    for _, raw_row in df.iterrows():
        row = map_row({k: "" if pd.isna(v) else str(v) for k, v in raw_row.items()})
        validation = validate_record(row, existing_ids)

        for issue in validation.issues:
            issue_breakdown[issue.error_type] = issue_breakdown.get(issue.error_type, 0) + 1

        record_id = int(float(row.get("record_id", 0) or 0))
        parsed_date = parse_date(row.get("tarih"))
        tarih_str = parsed_date.isoformat() if parsed_date else (row.get("tarih") or "")

        def fval(key):
            v = row.get(key, "")
            if v == "":
                return None
            try:
                return float(v.replace(",", "."))
            except ValueError:
                return None

        def ival(key):
            v = fval(key)
            return int(v) if v is not None else None

        record = ProductionRecord(
            record_id=record_id,
            tarih=tarih_str,
            is_emri_no=row.get("is_emri_no") or None,
            is_merkezi_no=row.get("is_merkezi_no") or None,
            ismerkezi_adi=row.get("ismerkezi_adi") or None,
            is_istasyon_adi=row.get("is_istasyon_adi") or None,
            stok_adi=row.get("stok_adi") or None,
            vardiya=ival("vardiya"),
            availability=fval("availability"),
            performance=fval("performance"),
            quality=fval("quality"),
            oee=fval("oee"),
            calisma_suresi=fval("calisma_suresi"),
            durus_suresi=fval("durus_suresi"),
            planli_durus=fval("planli_durus"),
            plansiz_durus=fval("plansiz_durus"),
            uretilen_miktar=ival("uretilen_miktar"),
            hatali_miktar=ival("hatali_miktar"),
            validation_status=validation.status,
            import_batch_id=batch_id,
            file_hash=fhash,
        )
        db.add(record)
        db.flush()

        for issue in validation.issues:
            db.add(
                ValidationIssue(
                    record_id=record_id,
                    production_record_id=record.id,
                    error_type=issue.error_type,
                    fields=",".join(issue.fields),
                    message=issue.message,
                    severity=issue.severity,
                    suggested_action=issue.suggested_action,
                    import_batch_id=batch_id,
                )
            )

        existing_ids.add(record_id)
        if validation.has_reject:
            rejected += 1
        elif validation.has_warn:
            warnings += 1
            imported += 1
        else:
            imported += 1

    batch = ImportBatch(
        id=batch_id,
        filename=filename,
        file_hash=fhash,
        total_rows=len(df),
        imported_rows=imported,
        rejected_rows=rejected,
        warning_rows=warnings,
    )
    db.add(batch)
    db.commit()

    return {
        "duplicate": False,
        "batch_id": batch_id,
        "summary": {
            "total_rows": len(df),
            "imported_rows": imported,
            "rejected_rows": rejected,
            "warning_rows": warnings,
            "issue_breakdown": issue_breakdown,
        },
    }


def update_record(db: Session, record_id: int, updates: dict, action: str = "manual_fix") -> ProductionRecord:
    record = db.query(ProductionRecord).filter(ProductionRecord.record_id == record_id).first()
    if not record:
        raise ValueError("Kayıt bulunamadı")

    allowed = {
        "tarih", "is_emri_no", "is_merkezi_no", "ismerkezi_adi", "is_istasyon_adi",
        "stok_adi", "vardiya", "availability", "performance", "quality", "oee",
        "calisma_suresi", "durus_suresi", "planli_durus", "plansiz_durus",
        "uretilen_miktar", "hatali_miktar", "validation_status",
    }

    row = {
        "record_id": str(record.record_id),
        "tarih": record.tarih,
        "is_emri_no": record.is_emri_no or "",
        "is_merkezi_no": record.is_merkezi_no or "",
        "ismerkezi_adi": record.ismerkezi_adi or "",
        "is_istasyon_adi": record.is_istasyon_adi or "",
        "stok_adi": record.stok_adi or "",
        "vardiya": str(record.vardiya or ""),
        "availability": str(record.availability if record.availability is not None else ""),
        "performance": str(record.performance if record.performance is not None else ""),
        "quality": str(record.quality if record.quality is not None else ""),
        "oee": str(record.oee if record.oee is not None else ""),
        "calisma_suresi": str(record.calisma_suresi if record.calisma_suresi is not None else ""),
        "durus_suresi": str(record.durus_suresi if record.durus_suresi is not None else ""),
        "planli_durus": str(record.planli_durus if record.planli_durus is not None else ""),
        "plansiz_durus": str(record.plansiz_durus if record.plansiz_durus is not None else ""),
        "uretilen_miktar": str(record.uretilen_miktar if record.uretilen_miktar is not None else ""),
        "hatali_miktar": str(record.hatali_miktar if record.hatali_miktar is not None else ""),
    }

    for key, value in updates.items():
        if key not in allowed:
            continue
        old = getattr(record, key)
        setattr(record, key, value)
        row[key] = str(value if value is not None else "")
        db.add(
            AuditLog(
                record_id=record_id,
                field_name=key,
                old_value=str(old) if old is not None else None,
                new_value=str(value) if value is not None else None,
                action=action,
            )
        )

    if action == "reject":
        record.validation_status = "rejected"
    else:
        validation = validate_record(row)
        record.validation_status = validation.status
        db.query(ValidationIssue).filter(
            ValidationIssue.production_record_id == record.id
        ).update({"resolved": True})
        for issue in validation.issues:
            db.add(
                ValidationIssue(
                    record_id=record_id,
                    production_record_id=record.id,
                    error_type=issue.error_type,
                    fields=",".join(issue.fields),
                    message=issue.message,
                    severity=issue.severity,
                    suggested_action=issue.suggested_action,
                    import_batch_id=record.import_batch_id,
                )
            )

    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record
