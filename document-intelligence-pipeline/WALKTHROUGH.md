# Walkthrough — Turkish Invoice & Contract Intelligence Platform

## Proje Özeti

**Repo:** `document-intelligence-pipeline`  
**Tarih:** Eylül 2026  
**Stack:** Python 3.11 · FastAPI · RQ + Redis · Streamlit · Docker · GitHub Actions

---

## Yapılan İşler

### 1. Proje Yapısı

```
document-intelligence-pipeline/
├── src/                   # Tüm iş mantığı
├── api/                   # FastAPI backend
├── dashboard/             # Streamlit paneli
├── samples/               # 7 örnek PDF (programatik)
├── tests/                 # 68 test + evaluation
└── docker-compose.yml     # 4 servis: redis, api, worker, dashboard
```

### 2. Extraction Katmanı

- **`PDFExtractor`**: `pdfplumber` ile metin + tablo çıkarımı, `PyMuPDF` ile bounding box desteği
- **`DocxExtractor`**: `python-docx` ile başlık hiyerarşisi + paragraf + tablo çıkarımı
- **`TableExtractor`**: Türkçe sayı formatı (`1.234,56`) ve plain decimal (`1234.56`) desteği

### 3. Sınıflandırma

- `DocumentClassifier`: Ağırlıklı keyword scoring ile `invoice | contract | technical | unknown`
- Güven skoru (`confidence: float`) ve `uncertain` flag
- 7/7 örnek belgede %100 doğruluk

### 4. Alan Çıkarımı (Parsers)

| Parser | Alan Sayısı | Yaklaşım |
|---|---|---|
| `InvoiceParser` | 14 | Regex + tablo satır eşleştirme |
| `ContractParser` | 12 | Regex + çok-eşleşme (fesih maddeleri) |
| `TechnicalDocParser` | 10 | Başlık hiyerarşisi + anahtar kelime |

### 5. Evidence / Citation Builder

Her çıkarılan alan için:
- Sayfa numarası
- Context snippet (±40 karakter)
- Opsiyonel bounding box (PyMuPDF ile)
- Güven skoru

### 6. Doğrulama

`FieldValidator`:
- Zorunlu alan eksikliği (error)
- VKN/IBAN/sözleşme no format kontrolü (warning)
- Fatura matematik tutarsızlığı: `ara_toplam × (1 + kdv%) ≠ toplam_tutar` (warning)
- Tarih sırası: bitiş < başlangıç (warning)

### 7. FastAPI Backend

```
POST /api/v1/upload          → job_id (Redis kuyruğa alır veya sync çalışır)
GET  /api/v1/status/{id}     → queued | processing | done | failed
GET  /api/v1/result/{id}     → tam PipelineResult JSON
GET  /api/v1/result/{id}/fields   → yalnızca çıkarılan alanlar
GET  /api/v1/result/{id}/evidence → yalnızca kaynak atıflar
GET  /health                 → {"status": "ok"}
```

Redis yoksa otomatik senkron fallback (dosya tabanlı).

### 8. RQ + Redis Worker Queue

- `rq` kütüphanesi, `documents` kuyruğu
- Job timeout: 120 sn
- Sonuç TTL: 1 saat (Redis key expiry)
- `docker-compose` içinde `worker` servisi

### 9. Streamlit Dashboard

3 sekme:
- **Upload & Process**: Dosya yükle → KPI kartları → Ham JSON
- **Results & Evidence**: Alanlar + atıflar + doğrulama sorunları
- **Evaluation Report**: Tüm sample belgeleri pipeline'dan geçirip F1 raporu

### 10. Sample PDFs

`reportlab` ile 7 kurgusal ama gerçekçi Türkçe PDF:
- 3 Fatura (tam, USD, eksik)
- 2 Sözleşme (Hizmet, NDA)
- 2 Teknik Doküman (API dok., Kurulum kılavuzu)

### 11. Test Suite

```
68 passed in 74.68s
```

- `test_api.py` — 9 test (FastAPI TestClient, sync fallback)
- `test_classifiers.py` — 13 test (metin + 6 PDF)
- `test_extractors.py` — 13 test (bbox, tablo, numerik)
- `test_parsers.py` — 24 test (parser + validator)
- `test_pipeline.py` — 9 test (uçtan uca)

### 12. Evaluation

```
INVOICE    P=1.00  R=0.75  F1=0.86
CONTRACT   P=1.00  R=0.86  F1=0.92
TECHNICAL  P=1.00  R=1.00  F1=1.00
─────────────────────────────────────
OVERALL    P=1.00  R=0.84  F1=0.91
```

Classification: 7/7 = 100%

### 13. Docker & CI

```yaml
# docker-compose.yml
services: redis, api, worker, dashboard

# .github/workflows/ci.yml
jobs: test, lint (ruff), docker-build
```

---

## Bilinen Sınırlamalar

1. **PDF font encoding**: `reportlab` built-in font Türkçe karakterleri (`ş→n`, `İ→n`) doğru encode etmez. Gerçek belgeler (tarayıcı, Word, e-Devlet) bu sorunu yaşamaz.
2. **Regex extraction sınırları**: Formatı tamamen farklı belgeler bazı alanları kaçırabilir. LLM katmanı eklendiğinde recall önemli ölçüde artacaktır.
3. **Redis olmadan worker yok**: Sync fallback otomatik devreye girer; distributed worker için Redis gereklidir.

---

## Git Commit

İlk commit: `document-intelligence-pipeline v1.0.0`
- 68/68 test geçti
- F1=0.91 evaluation geçti
- 7 örnek PDF dahil
