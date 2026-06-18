# AI Kullanım Şeffaflık Kaydı — MAGNA Case Study

**Aday:** İrem Çınar  
**Proje:** Üretim Performans Takip Uygulaması  
**Tarih:** Haziran 2026


Bu dosya, projede kullanılan yapay zeka araçlarını, verilen promptları ve alınan cevapların nasıl uygulandığını tek yerde toplar. Farklı yapay zeka araçlarından geliştirme sürecinin farklı aşamalarında yararlanılmıştır. Mimari kararlar, validasyon yaklaşımı ve UI fikirleri ağırlıklı olarak ChatGPT, Gemini ve v0 ile değerlendirilmiş; Cursor ise geliştirme sırasında kod tamamlama, refactoring ve hata giderme amaçlı kullanılmıştır.

---

## Harici AI Sohbet Linkleri

| Araç | Konu | Link |
|------|------|------|
| **ChatGPT** | Veri modeli & SQLite şema incelemesi | https://chatgpt.com/share/6a33bb1b-4d24-83ed-b0c3-db8c7bf036e1 |
| **v0 (Vercel)** | Validasyon raporu UI tasarımı | https://v0.app/chat/validation-report-analysis-fzxE9TVL8V4?ref=B9ICWR |
| **Google Gemini** | Validasyon kuralları & OEE mantığı | https://gemini.google.com/share/fc0e9dfa7a48 |

---

## Cursor IDE 



### Prompt C1 — Paralel HTTP
> `sync_service.py`'de 54 istek sırayla gidiyor ve UI donuyor. Mevcut koduma `asyncio.Semaphore(5)` ile paralel POST eklemek mantıklı mı?

**Cevap (özet):** Evet; HTTP darboğaz. Semaphore ile eşzamanlılık sınırla, idempotency kontrolünü döngü öncesinde toplu yap, DB commit'i tek seferde bırak.

**Uygulama:** `backend/services/sync_service.py` — paralel gönderim ve arka plan job

---

### Prompt C2 — Python 3.9 uyumluluğu
> Pydantic modelde `str | None` kullanınca Python 3.9'da `TypeError: unsupported operand type(s) for |` alıyorum. En küçük düzeltme ne?

**Cevap (özet):** `from typing import Optional` ile `Optional[str]` kullan; router parametrelerinde de aynı.

**Uygulama:** `backend/schemas/production.py`, `backend/routers/`

---

### Prompt C3 — DataTable bileşeni
> `RecordsPage.tsx`'teki tabloya asc/desc sıralama ve sayfa başına 10 satır pagination eklemek istiyorum. Sunucu tarafı `skip/limit` zaten var — ortak bir `DataTable` bileşeni nasıl kurgulanır?

**Cevap (özet):** Sort state + server mode props (`total`, `page`, `onSortChange`); kayıtlar sunucu, validasyon istemci tarafı.

**Uygulama:** `frontend/src/components/DataTable.tsx`

---

### Cursor sohbet ekran görüntüsü

![Cursor — dar kapsamlı refactoring soruları](cursor_chat.png)

---

## Bölüm 1 — Veri Modeli & Mimari (ChatGPT)

### Prompt 1
> MAGNA case study için production_data.csv dosyasını SQLite'a aktaracağım. 2117 satır, 18 kolon. Hangi tabloları oluşturmalıyım? Validasyon hataları, import batch, audit trail ve API sync geçmişi de saklanmalı.

### Cevap (özet)
ChatGPT şu tabloları önerdi:
- `production_records` — normalize edilmiş üretim satırları + `validation_status`
- `validation_issues` — hata tipi, severity, suggested_action
- `audit_logs` — manuel düzeltme geçmişi
- `import_batches` — dosya hash ile duplicate kontrolü
- `sync_submissions` — tarih+vardiya bazlı idempotent API gönderimi

**Projede uygulama:** `backend/models/production.py`

---

### Prompt 2
> FastAPI + React mi yoksa Streamlit mi? Case study React tercih ediyor ama 2 gün sürem var.

### Cevap (özet)
- Backend: **FastAPI** (OpenAPI docs, async, Pydantic)
- Frontend: **React + Vite + TypeScript**
- DB: **SQLite** (zorunlu)
- Validasyon mantığı backend'de; frontend sadece UI

**Projede uygulama:** `backend/main.py`, `frontend/src/App.tsx`

---

## Bölüm 2 — Validasyon Kuralları (Gemini)

### Prompt 3
> production_data.csv'de OEE = A×P×Q/10000 formülü var. P>100 olan 787 kayıt var — bunlar hata mı? Fire üretimden fazla olan kayıtlar?

### Cevap (özet)
Gemini şu sınıflandırmayı önerdi:

| Durum | Severity | Gerekçe |
|-------|----------|---------|
| `SCRAP_EXCEEDS_PRODUCTION` | **reject** | Fiziksel olarak imkânsız |
| `MISSING_SHIFT`, `INVALID_SHIFT` | **reject** | Zorunlu alan |
| `PERFORMANCE_OVER_100`, `OEE_OVER_100` | **warn** | MES'te ideal hız aşımı yaygın |
| `OEE_FORMULA_MISMATCH` | **warn/fix** | Tolerans ±0.15 |
| `MISSING_PRODUCT` | **warn** | Raporlama için eksik |

**Projede uygulama:** `backend/services/validation_service.py` (20+ kural)

---

### Prompt 4
> CSV'de Türkçe karakter bozuk — `?? Emri No`, cp1254 encoding. Import sırasında kolonları nasıl eşleştireyim?

### Cevap (özet)
- Encoding sırası: `utf-8-sig` → `cp1254` → `latin-1`
- Canonical column mapping (fuzzy header match)
- Pandas float iş emri numaralarını `3027854094.0` yapıyor → `.0` strip et

**Projede uygulama:** `backend/services/csv_parser.py`

---

## Bölüm 3 — Validasyon UI (v0)

### Prompt 5
> Validasyon raporu sayfası tasarla: hata tipi dağılım kartları, reject/warn filtresi, tabloda record_id / hata tipi / mesaj / düzelt-reddet aksiyonları.

### Cevap (özet)
v0 şu layout'u önerdi:
- Üst: özet KPI + Tümü / Reddedilen / Uyarı toggle
- Orta: hata tipi breakdown grid
- Alt: sortable tablo + modal ile manuel düzeltme

**Projede uygulama:** `frontend/src/pages/ValidationPage.tsx`

---

## Bölüm 4 — CSV Import & Dashboard

### Prompt 6
> Import akışı: drag-drop, ilk 10 satır preview, duplicate file kontrolü, import sonrası özet (toplam/import/reject/warning + hata dağılımı).

### Cevap (özet)
- SHA-256 file hash → `import_batches` duplicate check
- Preview endpoint ayrı (`POST /import/preview`)
- Upload endpoint validate edip özet döner

**Projede uygulama:** `backend/services/import_service.py`, `frontend/src/pages/ImportPage.tsx`

---

### Prompt 7
> Dashboard'da OEE trend (günlük), vardiya karşılaştırma, istasyon sıralaması, fire oranı dağılımı ve KPI kartları lazım.

### Cevap (özet)
- Recharts: LineChart (trend), BarChart (vardiya/istasyon/fire)
- OEE > 100 dashboard'da cap 100 (ortalama yanıltmasın)
- Rejected kayıtlar grafiklere dahil edilmez

**Projede uygulama:** `frontend/src/pages/DashboardPage.tsx`, `backend/services/analytics_service.py`

---

## Bölüm 5 — Filtreleme & Kayıtlar

### Prompt 8
> Kayıtlar sayfasında tarih aralığı, çoklu vardiya, istasyon, ürün, OEE slider, sorunlu kayıt toggle ve CSV export istiyorum.

### Cevap (özet)
- Query params ile anlık filtreleme
- `GET /records/export` streaming CSV
- Filter options endpoint: distinct istasyon/ürün/tarih min-max

**Projede uygulama:** `frontend/src/pages/RecordsPage.tsx`, `backend/routers/records_router.py`

---

## Bölüm 6 — DataTable Sıralama & Sayfalama

### Prompt 9
> datatableların içine asc desc sıralama ekle ve pagination özelliği ekle (her sayfada 10 satır veri görünür ileri geri yaptıkça diğer veriler gelir)

### Cevap (özet)
- Ortak `DataTable` bileşeni: sortable header, 10 satır/sayfa, sayfa numaraları
- Kayıtlar: **sunucu tarafı** (`sort_by`, `sort_order`, `skip`, `limit=10`)
- Validasyon/Sync: **istemci tarafı** (tüm veri yüklü)

**Projede uygulama:** `frontend/src/components/DataTable.tsx` *(Cursor C3 ile implementasyon)*

---

## Bölüm 7 — API Senkronizasyon

### Prompt 10
> Temiz kayıtları MAGNA API'ye POST et: X-Production-Key header, tarih+vardiya bazlı aggregate, retry, idempotency. Endpoint: POST /api/v1/submit

### Cevap (özet)
- Aggregate: `machine_count`, `total_production_units`, `oe_value` (max 100), `shift`, `production_date`
- Idempotency key: SHA256(date:shift:api_key_prefix)
- Retry: exponential backoff, 429 için bekleme

**Projede uygulama:** `backend/services/sync_service.py`

---

### Prompt 11
> senkronize et butonuna basınca aşırı yavaş çalışıyor. nedeni ne olabilir ve nasıl düzeltilir

### Cevap (özet)
**Nedenler:** 54 sıralı HTTP isteği, UI blokajı, uzun timeout, N+1 DB sorgusu.

**Düzeltmeler:** Paralel istek, arka plan job, toplu idempotency, tek commit.

**Projede uygulama:** `sync_service.py`, `sync_router.py`, `SyncPage.tsx` *(Cursor C1 ile refactoring)*

---

## Bölüm 8 — Test & Dokümantasyon

### Prompt 12
> Validasyon mantığı için pytest unit testleri yaz. Hangi senaryoları test etmeliyim?

### Cevap (özet)
- Geçerli kayıt → `valid`
- Eksik vardiya → `reject`
- Fire > üretim → `SCRAP_EXCEEDS_PRODUCTION`
- P > 100 → `warning` (reject değil)
- Geçersiz iş emri formatı

**Projede uygulama:** `backend/tests/test_validation.py` (5 test)

---

## Özet Tablo

| # | Konu | AI Aracı | Proje dosyası |
|---|------|----------|---------------|
| 1 | Veri modeli | ChatGPT | `models/production.py` |
| 2 | Stack seçimi | ChatGPT | `main.py`, `App.tsx` |
| 3 | Validasyon kuralları | Gemini | `validation_service.py` |
| 4 | CSV encoding | Gemini | `csv_parser.py` |
| 5 | Validasyon UI | v0 | `ValidationPage.tsx` |
| 6 | CSV import | ChatGPT | `import_service.py` |
| 7 | Dashboard | ChatGPT | `DashboardPage.tsx` |
| 8 | Filtreleme | ChatGPT | `RecordsPage.tsx` |
| 9 | DataTable | Cursor (C3) | `DataTable.tsx` |
| 10 | API sync | ChatGPT | `sync_service.py` |
| 11 | Sync performans | Cursor (C1) | `sync_service.py` |
| 12 | Py3.9 fix | Cursor (C2) | `schemas/production.py` |
| 13 | Unit testler | ChatGPT | `test_validation.py` |

---

## Dürüst Beyan

ChatGPT, Gemini ve v0 ağırlıklı olarak mimari kararlar, validasyon kuralları, kullanıcı arayüzü tasarımı ve teknik alternatiflerin değerlendirilmesi için kullanılmıştır.

Cursor IDE ise geliştirme sırasında kod tamamlama, refactoring, hata ayıklama ve bazı performans iyileştirmeleri için kullanılmıştır.

Tüm nihai mimari kararlar, validasyon kuralları ve uygulama davranışları tarafımdan değerlendirilmiş ve uygulanmıştır.


