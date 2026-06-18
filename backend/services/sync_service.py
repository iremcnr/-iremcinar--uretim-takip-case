from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

import httpx
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models.production import ProductionRecord, SyncSubmission

# In-memory job tracker (case study MVP — production'da Redis/Celery kullanılmalı)
_sync_jobs: dict[str, dict[str, Any]] = {}

CONCURRENT_REQUESTS = 5
HTTP_TIMEOUT = 12.0


def _idempotency_key(production_date: str, shift: int) -> str:
    raw = f"{production_date}:{shift}:{settings.api_key[:8]}"
    return hashlib.sha256(raw.encode()).hexdigest()


def aggregate_for_sync(db: Session) -> list[dict]:
    rows = (
        db.query(
            ProductionRecord.tarih,
            ProductionRecord.vardiya,
            func.count(func.distinct(ProductionRecord.is_istasyon_adi)).label("machine_count"),
            func.sum(ProductionRecord.uretilen_miktar).label("total_units"),
            func.avg(
                case(
                    (ProductionRecord.oee > 100, 100),
                    else_=ProductionRecord.oee,
                )
            ).label("avg_oee"),
        )
        .filter(ProductionRecord.validation_status.in_(["valid", "warning"]))
        .filter(ProductionRecord.vardiya.in_([1, 2, 3]))
        .filter(ProductionRecord.uretilen_miktar > 0)
        .group_by(ProductionRecord.tarih, ProductionRecord.vardiya)
        .all()
    )

    payloads = []
    for row in rows:
        date_str = row.tarih[:10] if row.tarih else ""
        shift = int(row.vardiya)
        machine_count = max(int(row.machine_count or 1), 1)
        total_units = max(int(row.total_units or 0), 1)
        oe_value = round(min(float(row.avg_oee or 0), 100.0), 1)
        oe_value = max(oe_value, 0.1)

        payloads.append(
            {
                "production_date": date_str,
                "shift": shift,
                "machine_count": machine_count,
                "total_production_units": total_units,
                "oe_value": oe_value,
                "idempotency_key": _idempotency_key(date_str, shift),
            }
        )
    return payloads


async def _post_with_retry(client: httpx.AsyncClient, payload: dict) -> dict:
    url = f"{settings.api_base_url.rstrip('/')}/api/v1/submit"
    headers = {
        "Content-Type": "application/json",
        "X-Production-Key": settings.api_key,
    }
    body = {k: v for k, v in payload.items() if k != "idempotency_key"}
    last_error = None

    for attempt in range(settings.sync_max_retries + 1):
        try:
            response = await client.post(url, json=body, headers=headers, timeout=HTTP_TIMEOUT)
            if response.status_code == 429:
                await asyncio.sleep(min(15, 60))  # rate limit — kısa bekleme
                continue
            if response.status_code >= 500 and attempt < settings.sync_max_retries:
                await asyncio.sleep(settings.sync_retry_delay_seconds * (2**attempt))
                continue
            return {
                "status_code": response.status_code,
                "body": response.text,
                "success": response.status_code == 200,
            }
        except httpx.HTTPError as exc:
            last_error = str(exc)
            if attempt < settings.sync_max_retries:
                await asyncio.sleep(settings.sync_retry_delay_seconds * (2**attempt))

    return {"status_code": 0, "body": last_error or "Unknown error", "success": False}


async def _post_batch(
    client: httpx.AsyncClient,
    payloads: list[dict],
    sem: asyncio.Semaphore,
    on_progress: Optional[Callable[[], None]] = None,
) -> list[tuple[dict, dict]]:
    """Paralel HTTP gönderimi — en büyük darboğazı giderir."""

    async def one(payload: dict) -> tuple[dict, dict]:
        async with sem:
            result = await _post_with_retry(client, payload)
            if on_progress:
                on_progress()
            return payload, result

    return await asyncio.gather(*[one(p) for p in payloads])


def get_job(job_id: str) -> Optional[dict]:
    return _sync_jobs.get(job_id)


def start_sync_job() -> str:
    job_id = str(uuid.uuid4())
    _sync_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "total": 0,
        "message": "Başlatılıyor...",
        "result": None,
    }
    return job_id


async def run_sync_job(job_id: str) -> None:
    job = _sync_jobs[job_id]
    db = SessionLocal()

    try:
        if not settings.api_key:
            job.update(
                {
                    "status": "failed",
                    "message": "API key yapılandırılmamış. .env dosyasını kontrol edin.",
                    "result": {"success": False, "results": []},
                }
            )
            return

        payloads = aggregate_for_sync(db)
        keys = [p["idempotency_key"] for p in payloads]
        existing_map = {
            s.idempotency_key: s
            for s in db.query(SyncSubmission).filter(SyncSubmission.idempotency_key.in_(keys)).all()
        }

        to_send: list[dict] = []
        results: list[dict] = []
        skipped = 0

        for payload in payloads:
            existing = existing_map.get(payload["idempotency_key"])
            if existing and existing.status == "success":
                skipped += 1
                results.append(
                    {
                        "production_date": payload["production_date"],
                        "shift": payload["shift"],
                        "status": "skipped",
                        "message": "Daha önce başarıyla gönderildi (idempotent).",
                        "submission_id": existing.submission_id,
                    }
                )
            else:
                to_send.append(payload)

        job.update(
            {
                "status": "running",
                "total": len(to_send),
                "progress": 0,
                "message": f"{len(to_send)} batch gönderiliyor ({skipped} atlandı)...",
            }
        )

        if not to_send:
            job["status"] = "completed"
            job["result"] = {
                "success": True,
                "success_count": 0,
                "fail_count": 0,
                "skipped_count": skipped,
                "total_batches": len(payloads),
                "results": results,
            }
            job["message"] = "Gönderilecek yeni batch yok (hepsi daha önce gönderilmiş)."
            return

        def tick():
            job["progress"] = min(job["progress"] + 1, job["total"])

        sem = asyncio.Semaphore(CONCURRENT_REQUESTS)
        async with httpx.AsyncClient() as client:
            batch_results = await _post_batch(client, to_send, sem, on_progress=tick)

        success_count = fail_count = 0
        for payload, response in batch_results:
            existing = existing_map.get(payload["idempotency_key"])
            submission = existing or SyncSubmission(
                production_date=payload["production_date"],
                shift=payload["shift"],
                machine_count=payload["machine_count"],
                total_production_units=payload["total_production_units"],
                oe_value=payload["oe_value"],
                idempotency_key=payload["idempotency_key"],
            )
            submission.machine_count = payload["machine_count"]
            submission.total_production_units = payload["total_production_units"]
            submission.oe_value = payload["oe_value"]
            submission.retry_count = (submission.retry_count or 0) + 1
            submission.response_body = response["body"]

            if response["success"]:
                submission.status = "success"
                submission.submitted_at = datetime.utcnow()
                try:
                    data = json.loads(response["body"])
                    submission.submission_id = data.get("submission_id")
                except json.JSONDecodeError:
                    pass
                success_count += 1
                results.append(
                    {
                        "production_date": payload["production_date"],
                        "shift": payload["shift"],
                        "status": "success",
                        "submission_id": submission.submission_id,
                        "message": "Başarıyla gönderildi.",
                    }
                )
            else:
                submission.status = "failed"
                submission.error_message = response["body"][:500]
                fail_count += 1
                results.append(
                    {
                        "production_date": payload["production_date"],
                        "shift": payload["shift"],
                        "status": "failed",
                        "status_code": response["status_code"],
                        "message": response["body"][:200],
                    }
                )

            if not existing:
                db.add(submission)

        db.commit()

        job["status"] = "completed"
        job["result"] = {
            "success": fail_count == 0,
            "success_count": success_count,
            "fail_count": fail_count,
            "skipped_count": skipped,
            "total_batches": len(payloads),
            "results": results,
        }
        job["message"] = f"Tamamlandı: {success_count} başarılı, {fail_count} başarısız, {skipped} atlandı."

    except Exception as exc:
        job["status"] = "failed"
        job["message"] = str(exc)
        job["result"] = {"success": False, "results": []}
    finally:
        db.close()


async def sync_clean_data(db: Session) -> dict:
    """Senkron (eski) endpoint — arka plan job başlatır ve bitene kadar bekler."""
    job_id = start_sync_job()
    await run_sync_job(job_id)
    job = get_job(job_id)
    return job.get("result") or {"success": False, "message": job.get("message"), "results": []}


def get_sync_history(db: Session) -> list[SyncSubmission]:
    return db.query(SyncSubmission).order_by(SyncSubmission.created_at.desc()).all()
