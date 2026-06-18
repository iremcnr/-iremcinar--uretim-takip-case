from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ProductionRecord(Base):
    __tablename__ = "production_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    tarih: Mapped[str] = mapped_column(String(20), index=True)
    is_emri_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_merkezi_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ismerkezi_adi: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_istasyon_adi: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    stok_adi: Mapped[Optional[str]] = mapped_column(String(300), nullable=True, index=True)
    vardiya: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    availability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    performance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    oee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calisma_suresi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    durus_suresi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    planli_durus: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    plansiz_durus: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    uretilen_miktar: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hatali_miktar: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    validation_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    import_batch_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, index=True)
    production_record_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    error_type: Mapped[str] = mapped_column(String(80), index=True)
    fields: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    suggested_action: Mapped[str] = mapped_column(String(20))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    import_batch_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, index=True)
    field_name: Mapped[str] = mapped_column(String(80))
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)
    warning_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SyncSubmission(Base):
    __tablename__ = "sync_submissions"
    __table_args__ = (UniqueConstraint("production_date", "shift", name="uq_sync_date_shift"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    production_date: Mapped[str] = mapped_column(String(10), index=True)
    shift: Mapped[int] = mapped_column(Integer, index=True)
    machine_count: Mapped[int] = mapped_column(Integer)
    total_production_units: Mapped[int] = mapped_column(Integer)
    oe_value: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    submission_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
