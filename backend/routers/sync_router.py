from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.production import SyncHistoryOut
from services.sync_service import (
    aggregate_for_sync,
    get_job,
    get_sync_history,
    run_sync_job,
    start_sync_job,
)

router = APIRouter(prefix="/sync", tags=["API Sync"])


@router.get("/preview")
def sync_preview(db: Session = Depends(get_db)):
    payloads = aggregate_for_sync(db)
    return {"count": len(payloads), "payloads": payloads}


@router.post("")
async def trigger_sync(background_tasks: BackgroundTasks):
    """Arka planda başlat — hemen job_id döner, UI poll eder."""
    job_id = start_sync_job()
    background_tasks.add_task(run_sync_job, job_id)
    return {"job_id": job_id, "status": "started", "message": "Senkronizasyon arka planda başlatıldı."}


@router.post("/sync-blocking")
async def trigger_sync_blocking(db: Session = Depends(get_db)):
    """Eski davranış: tüm istekler bitene kadar bekler (yavaş)."""
    from services.sync_service import sync_clean_data

    return await sync_clean_data(db)


@router.get("/jobs/{job_id}")
def sync_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job bulunamadı")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "total": job.get("total", 0),
        "message": job.get("message", ""),
        "result": job.get("result") if job["status"] in ("completed", "failed") else None,
    }


@router.get("/history", response_model=list[SyncHistoryOut])
def sync_history(db: Session = Depends(get_db)):
    return get_sync_history(db)
