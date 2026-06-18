"""Production data validation engine — core evaluation criteria for the case study."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from dateutil import parser as date_parser

WORK_ORDER_PATTERN = re.compile(r"^302\d{7}$")
OEE_TOLERANCE = 0.15
DOWNTIME_TOLERANCE = 0.05


@dataclass
class ValidationResult:
    error_type: str
    fields: list[str]
    message: str
    severity: str  # reject | warn | info
    suggested_action: str  # reject | warn | fix


@dataclass
class RecordValidation:
    issues: list[ValidationResult] = field(default_factory=list)

    @property
    def has_reject(self) -> bool:
        return any(i.severity == "reject" for i in self.issues)

    @property
    def has_warn(self) -> bool:
        return any(i.severity == "warn" for i in self.issues)

    @property
    def status(self) -> str:
        if self.has_reject:
            return "rejected"
        if self.has_warn:
            return "warning"
        return "valid"


def _parse_float(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    f = _parse_float(value)
    return int(f) if f is not None else None


def parse_date(value: str | None) -> date | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return date_parser.parse(text, dayfirst=False).date()
    except (ValueError, OverflowError):
        return None


def validate_record(row: dict, existing_record_ids: set[int] | None = None) -> RecordValidation:
    """Run all validation rules against a normalized CSV row."""
    result = RecordValidation()
    existing_record_ids = existing_record_ids or set()

    def add(
        error_type: str,
        fields: list[str],
        message: str,
        severity: str = "reject",
        suggested_action: str | None = None,
    ):
        result.issues.append(
            ValidationResult(
                error_type=error_type,
                fields=fields,
                message=message,
                severity=severity,
                suggested_action=suggested_action or severity,
            )
        )

    # --- record_id ---
    record_id = _parse_int(row.get("record_id"))
    if record_id is None:
        add("MISSING_RECORD_ID", ["record_id"], "record_id alanı zorunludur.")
    elif record_id in existing_record_ids:
        add("DUPLICATE_RECORD_ID", ["record_id"], f"record_id {record_id} veritabanında zaten mevcut.")

    # --- tarih ---
    tarih_raw = row.get("tarih")
    parsed_date = parse_date(tarih_raw)
    if not tarih_raw:
        add("MISSING_DATE", ["tarih"], "Tarih alanı boş.")
    elif parsed_date is None:
        add("INVALID_DATE_FORMAT", ["tarih"], f"Tarih formatı tanınamadı: '{tarih_raw}'")
    elif parsed_date > date.today():
        add("FUTURE_DATE", ["tarih"], "Gelecek tarihli kayıt kabul edilmez.")

    # --- iş emri ---
    is_emri = (row.get("is_emri_no") or "").strip()
    if not is_emri:
        add("MISSING_WORK_ORDER", ["is_emri_no"], "İş emri numarası boş.")
    elif not WORK_ORDER_PATTERN.match(is_emri):
        add(
            "INVALID_WORK_ORDER_FORMAT",
            ["is_emri_no"],
            f"İş emri 302 ile başlayan 10 haneli olmalı, bulunan: '{is_emri}'",
        )

    # --- iş merkezi / istasyon ---
    if not (row.get("is_merkezi_no") or "").strip():
        add(
            "MISSING_WORK_CENTER",
            ["is_merkezi_no"],
            "İş merkezi numarası boş.",
            severity="warn",
            suggested_action="warn",
        )
    if not (row.get("is_istasyon_adi") or "").strip():
        add("MISSING_WORKSTATION", ["is_istasyon_adi"], "İş istasyonu adı boş.")

    # --- stok ---
    if not (row.get("stok_adi") or "").strip():
        add(
            "MISSING_PRODUCT",
            ["stok_adi"],
            "Stok/ürün adı boş — üretim raporlaması için gerekli.",
            severity="warn",
            suggested_action="warn",
        )

    # --- vardiya ---
    vardiya_raw = (row.get("vardiya") or "").strip()
    vardiya = _parse_int(vardiya_raw)
    if not vardiya_raw:
        add("MISSING_SHIFT", ["vardiya"], "Vardiya numarası boş.")
    elif vardiya not in (1, 2, 3):
        add("INVALID_SHIFT", ["vardiya"], f"Vardiya 1, 2 veya 3 olmalı, bulunan: '{vardiya_raw}'")

    # --- yüzde alanları ---
    a = _parse_float(row.get("availability"))
    p = _parse_float(row.get("performance"))
    q = _parse_float(row.get("quality"))
    oee = _parse_float(row.get("oee"))

    if a is not None and (a < 0 or a > 100):
        add("AVAILABILITY_OUT_OF_RANGE", ["availability"], f"A (Kullanılabilirlik) 0-100 arası olmalı: {a}")
    if q is not None and (q < 0 or q > 100):
        add("QUALITY_OUT_OF_RANGE", ["quality"], f"Q (Kalite) 0-100 arası olmalı: {q}")
    if p is not None and p < 0:
        add("PERFORMANCE_NEGATIVE", ["performance"], f"P (Performans) negatif olamaz: {p}")
    if p is not None and p > 100:
        add(
            "PERFORMANCE_OVER_100",
            ["performance"],
            f"P (Performans) %100'ü aşıyor ({p:.2f}) — ideal hız aşımı, MES'te yaygın.",
            severity="warn",
            suggested_action="warn",
        )
    if oee is not None and oee < 0:
        add("OEE_NEGATIVE", ["oee"], f"OEE negatif olamaz: {oee}")
    if oee is not None and oee > 100:
        add(
            "OEE_OVER_100",
            ["oee"],
            f"OEE %100'ü aşıyor ({oee:.2f}) — genelde P>100 kaynaklı.",
            severity="warn",
            suggested_action="warn",
        )

    # --- OEE formül tutarlılığı ---
    if a is not None and p is not None and q is not None and oee is not None:
        calculated = round(a * p * q / 10000, 2)
        if abs(calculated - oee) > OEE_TOLERANCE:
            add(
                "OEE_FORMULA_MISMATCH",
                ["oee", "availability", "performance", "quality"],
                f"OEE ({oee}) ≠ A×P×Q/10000 ({calculated:.2f}).",
                severity="warn",
                suggested_action="fix",
            )

    # --- üretim / fire ---
    prod = _parse_int(row.get("uretilen_miktar"))
    scrap = _parse_int(row.get("hatali_miktar"))

    if prod is not None and prod < 0:
        add("NEGATIVE_PRODUCTION", ["uretilen_miktar"], "Üretilen miktar negatif olamaz.")
    if scrap is not None and scrap < 0:
        add("NEGATIVE_SCRAP", ["hatali_miktar"], "Hatalı üretim miktarı negatif olamaz.")
    if prod is not None and scrap is not None and scrap > prod:
        add(
            "SCRAP_EXCEEDS_PRODUCTION",
            ["hatali_miktar", "uretilen_miktar"],
            f"Fire ({scrap}) üretimden ({prod}) fazla — fiziksel olarak imkânsız.",
        )

    # --- kalite hesap tutarlılığı ---
    if prod and prod > 0 and q is not None:
        expected_q = round((prod - (scrap or 0)) / prod * 100, 2)
        if abs(expected_q - q) > 1.0:
            add(
                "QUALITY_CALC_MISMATCH",
                ["quality", "uretilen_miktar", "hatali_miktar"],
                f"Q ({q}) ≠ (Üretilen-Fire)/Üretilen×100 ({expected_q}).",
                severity="warn",
                suggested_action="fix",
            )

    # --- süre tutarlılığı ---
    cal = _parse_float(row.get("calisma_suresi"))
    dur = _parse_float(row.get("durus_suresi"))
    plan = _parse_float(row.get("planli_durus"))
    unplan = _parse_float(row.get("plansiz_durus"))

    for name, val in [
        ("calisma_suresi", cal),
        ("durus_suresi", dur),
        ("planli_durus", plan),
        ("plansiz_durus", unplan),
    ]:
        if val is not None and val < 0:
            add("NEGATIVE_DURATION", [name], f"{name} negatif olamaz: {val}")

    if plan is not None and unplan is not None and dur is not None:
        if abs((plan + unplan) - dur) > DOWNTIME_TOLERANCE and dur > 0:
            add(
                "DOWNTIME_SUM_MISMATCH",
                ["durus_suresi", "planli_durus", "plansiz_durus"],
                f"Planlı+Plansız ({plan + unplan:.2f}) ≠ Duruş ({dur:.2f}).",
                severity="warn",
                suggested_action="warn",
            )

    # --- availability mantığı ---
    if cal is not None and unplan is not None and (cal + unplan) > 0 and a is not None:
        expected_a = round(cal / (cal + unplan) * 100, 2)
        if abs(expected_a - a) > 2.0 and a > 0:
            add(
                "AVAILABILITY_CALC_MISMATCH",
                ["availability", "calisma_suresi", "plansiz_durus"],
                f"A ({a}) ≠ Çalışma/(Çalışma+Plansız)×100 ({expected_a}).",
                severity="warn",
                suggested_action="warn",
            )

    # --- sıfır üretim + pozitif OEE ---
    if prod == 0 and oee is not None and oee > 0:
        add(
            "ZERO_PRODUCTION_POSITIVE_OEE",
            ["uretilen_miktar", "oee"],
            "Üretim sıfırken OEE pozitif — mantıksal tutarsızlık.",
            severity="warn",
            suggested_action="warn",
        )

    # --- sıfır süre + pozitif üretim ---
    if prod and prod > 0 and cal is not None and cal == 0:
        add(
            "ZERO_RUNTIME_WITH_PRODUCTION",
            ["calisma_suresi", "uretilen_miktar"],
            "Çalışma süresi sıfırken üretim var.",
            severity="warn",
            suggested_action="warn",
        )

    return result
