import pytest

from services.validation_service import validate_record


class TestValidation:
    def test_valid_record(self):
        row = {
            "record_id": "9999",
            "tarih": "11/5/2025",
            "is_emri_no": "3027854094",
            "is_merkezi_no": "INJECTION EXTERIORS",
            "is_istasyon_adi": "IMM-2700-3",
            "stok_adi": "Test Product",
            "vardiya": "1",
            "availability": "95",
            "performance": "90",
            "quality": "100",
            "oee": "85.5",
            "calisma_suresi": "100",
            "durus_suresi": "10",
            "planli_durus": "5",
            "plansiz_durus": "5",
            "uretilen_miktar": "50",
            "hatali_miktar": "0",
        }
        result = validate_record(row)
        assert result.status == "valid"

    def test_missing_shift_rejected(self):
        row = {
            "record_id": "19",
            "tarih": "11/5/2025",
            "is_emri_no": "3027011014",
            "is_istasyon_adi": "IMM-2700-3",
            "stok_adi": "Product",
            "vardiya": "",
            "availability": "8.98",
            "performance": "74.49",
            "quality": "100",
            "oee": "6.69",
            "uretilen_miktar": "8",
            "hatali_miktar": "0",
        }
        result = validate_record(row)
        assert result.has_reject
        assert any(i.error_type == "MISSING_SHIFT" for i in result.issues)

    def test_scrap_exceeds_production(self):
        row = {
            "record_id": "32",
            "tarih": "11/5/2025",
            "is_emri_no": "3021587258",
            "is_istasyon_adi": "IMM-2700-3",
            "stok_adi": "Product",
            "vardiya": "3",
            "availability": "0",
            "performance": "0",
            "quality": "0",
            "oee": "0",
            "uretilen_miktar": "0",
            "hatali_miktar": "3",
        }
        result = validate_record(row)
        assert any(i.error_type == "SCRAP_EXCEEDS_PRODUCTION" for i in result.issues)

    def test_performance_over_100_is_warning(self):
        row = {
            "record_id": "2",
            "tarih": "11/5/2025",
            "is_emri_no": "3029724496",
            "is_istasyon_adi": "IMM-2700-3",
            "stok_adi": "Product",
            "vardiya": "2",
            "availability": "100",
            "performance": "141.87",
            "quality": "100",
            "oee": "141.87",
            "uretilen_miktar": "3",
            "hatali_miktar": "0",
        }
        result = validate_record(row)
        assert result.status == "warning"
        assert any(i.error_type == "PERFORMANCE_OVER_100" for i in result.issues)

    def test_invalid_work_order(self):
        row = {
            "record_id": "100",
            "tarih": "11/5/2025",
            "is_emri_no": "12345",
            "is_istasyon_adi": "IMM-2700-1",
            "stok_adi": "Product",
            "vardiya": "1",
            "uretilen_miktar": "10",
            "hatali_miktar": "0",
        }
        result = validate_record(row)
        assert any(i.error_type == "INVALID_WORK_ORDER_FORMAT" for i in result.issues)
