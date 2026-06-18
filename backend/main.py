from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import import_router, records_router, sync_router

app = FastAPI(
    title="MAGNA Üretim Performans Takip API",
    description="Injection molding hattı OEE takip ve veri validasyon sistemi",
    version="1.0.0",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_router.router, prefix="/api")
app.include_router(records_router.router, prefix="/api")
app.include_router(sync_router.router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "uretim-takip"}
