from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RecordOut(BaseModel):
    id: int
    record_id: int
    tarih: str
    is_emri_no: Optional[str] = None
    is_merkezi_no: Optional[str] = None
    ismerkezi_adi: Optional[str] = None
    is_istasyon_adi: Optional[str] = None
    stok_adi: Optional[str] = None
    vardiya: Optional[int] = None
    availability: Optional[float] = None
    performance: Optional[float] = None
    quality: Optional[float] = None
    oee: Optional[float] = None
    calisma_suresi: Optional[float] = None
    durus_suresi: Optional[float] = None
    planli_durus: Optional[float] = None
    plansiz_durus: Optional[float] = None
    uretilen_miktar: Optional[int] = None
    hatali_miktar: Optional[int] = None
    validation_status: str
    import_batch_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ValidationIssueOut(BaseModel):
    id: int
    record_id: int
    error_type: str
    fields: str
    message: str
    severity: str
    suggested_action: str
    resolved: bool
    import_batch_id: Optional[str] = None

    model_config = {"from_attributes": True}


class RecordUpdate(BaseModel):
    tarih: Optional[str] = None
    is_emri_no: Optional[str] = None
    is_merkezi_no: Optional[str] = None
    ismerkezi_adi: Optional[str] = None
    is_istasyon_adi: Optional[str] = None
    stok_adi: Optional[str] = None
    vardiya: Optional[int] = None
    availability: Optional[float] = None
    performance: Optional[float] = None
    quality: Optional[float] = None
    oee: Optional[float] = None
    calisma_suresi: Optional[float] = None
    durus_suresi: Optional[float] = None
    planli_durus: Optional[float] = None
    plansiz_durus: Optional[float] = None
    uretilen_miktar: Optional[int] = None
    hatali_miktar: Optional[int] = None
    action: str = Field(default="manual_fix", description="manual_fix | reject | approve")


class RecordQuery(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    shifts: Optional[List[int]] = None
    stations: Optional[List[str]] = None
    products: Optional[List[str]] = None
    oee_min: Optional[float] = None
    oee_max: Optional[float] = None
    issues_only: bool = False
    skip: int = 0
    limit: int = 100


class SyncHistoryOut(BaseModel):
    id: int
    production_date: str
    shift: int
    machine_count: int
    total_production_units: int
    oe_value: float
    status: str
    submission_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int
    submitted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: int
    record_id: int
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}
