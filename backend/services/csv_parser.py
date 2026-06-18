"""CSV column normalization — handles Turkish encoding variants from MES exports."""

from __future__ import annotations

import pandas as pd

CANONICAL_COLUMNS = {
    "record_id": ["record_id"],
    "tarih": ["tarih", "date"],
    "is_emri_no": ["iş emri no", "is emri no", "?? emri no"],
    "is_merkezi_no": ["iş merkezi no", "is merkezi no", "?? merkezi no"],
    "ismerkezi_adi": ["işmerkezi adı", "ismerkezi adi", "??merkezi ad?"],
    "is_istasyon_adi": ["iş istasyon adı", "is istasyon adi", "?? ?stasyon ad?"],
    "stok_adi": ["stok adı", "stok adi", "stok ad?"],
    "vardiya": ["vardiya", "shift"],
    "availability": ["a (kullanılabilirlik)", "a (kullanilabilirlik)", "a (kullan?l?rl?k)"],
    "performance": ["p (performans)"],
    "quality": ["q (kalite)"],
    "oee": ["oee"],
    "calisma_suresi": ["çalışma süresi", "calisma suresi", "çal??ma süresi"],
    "durus_suresi": ["duruş süresi", "durus suresi", "duru? süresi"],
    "planli_durus": ["planlı duruş süresi", "planli durus suresi", "planl? duru? süresi"],
    "plansiz_durus": ["plansız duruş süresi", "plansiz durus suresi", "plans?z duru? süresi"],
    "uretilen_miktar": ["üretilen miktar", "uretilen miktar", "üretilen miktar"],
    "hatali_miktar": ["hatalı üretilen miktar", "hatali uretilen miktar", "hatal? üretilen miktar"],
}


def normalize_header(header: str) -> str | None:
    cleaned = header.strip().lower()
    for canonical, variants in CANONICAL_COLUMNS.items():
        if cleaned == canonical:
            return canonical
        for variant in variants:
            if cleaned == variant.lower():
                return canonical
    return None


def _clean_value(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text.replace(".0", "").isdigit():
        return text[:-2]
    return text


def map_row(raw: dict[str, str]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for key, value in raw.items():
        canonical = normalize_header(key)
        if canonical:
            mapped[canonical] = _clean_value(value)
    return mapped
