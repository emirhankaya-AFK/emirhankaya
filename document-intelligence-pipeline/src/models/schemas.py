"""
Pydantic v2 data models for the Document Intelligence Pipeline.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DocumentType(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    TECHNICAL = "technical"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Extraction layer
# ---------------------------------------------------------------------------

class PageText(BaseModel):
    page_number: int
    text: str
    tables: list[list[list[str]]] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    source_file: str
    total_pages: int
    pages: list[PageText]
    raw_text: str  # all pages joined


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    scores: dict[str, float] = Field(default_factory=dict)
    uncertain: bool = False


# ---------------------------------------------------------------------------
# Evidence / Citations
# ---------------------------------------------------------------------------

class FieldEvidence(BaseModel):
    field: str
    value: Any
    page: int
    snippet: str
    confidence: float = Field(ge=0.0, le=1.0)
    match_pattern: str = ""


# ---------------------------------------------------------------------------
# Parsed fields per document type
# ---------------------------------------------------------------------------

class InvoiceLineItem(BaseModel):
    description: str
    quantity: str = ""
    unit_price: str = ""
    total: str = ""


class InvoiceFields(BaseModel):
    fatura_no: str = ""
    tarih: str = ""
    vade_tarihi: str = ""
    satici_adi: str = ""
    satici_vkn: str = ""
    alici_adi: str = ""
    alici_vkn: str = ""
    kalemler: list[InvoiceLineItem] = Field(default_factory=list)
    ara_toplam: str = ""
    kdv_orani: str = ""
    kdv_tutari: str = ""
    toplam_tutar: str = ""
    para_birimi: str = "TRY"
    iban: str = ""
    odeme_kosullari: str = ""


class ContractParty(BaseModel):
    name: str
    role: str = ""
    vkn: str = ""
    address: str = ""


class ContractFields(BaseModel):
    sozlesme_no: str = ""
    sozlesme_turu: str = ""
    taraflar: list[ContractParty] = Field(default_factory=list)
    baslangic_tarihi: str = ""
    bitis_tarihi: str = ""
    sure: str = ""
    odeme_kosullari: str = ""
    fesih_sartlari: list[str] = Field(default_factory=list)
    ceza_klozu: str = ""
    gizlilik_maddesi: str = ""
    imza_tarihi: str = ""
    imzalayanlar: list[str] = Field(default_factory=list)


class TechnicalSection(BaseModel):
    title: str
    level: int = 1
    page: int = 1


class TechnicalDocFields(BaseModel):
    baslik: str = ""
    versiyon: str = ""
    yazar: str = ""
    tarih: str = ""
    kurulus: str = ""
    bolumler: list[TechnicalSection] = Field(default_factory=list)
    anahtar_kelimeler: list[str] = Field(default_factory=list)
    ozet: str = ""
    revizyon_gecmisi: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class ValidationIssue(BaseModel):
    issue_type: str  # "missing" | "conflict" | "format_error"
    field: str
    message: str
    severity: str = "warning"  # "error" | "warning"


class ValidationResult(BaseModel):
    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    format_errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pipeline output
# ---------------------------------------------------------------------------

class PipelineResult(BaseModel):
    job_id: str
    source_file: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    extraction: ExtractionResult
    classification: ClassificationResult
    fields: dict[str, Any]          # InvoiceFields | ContractFields | TechnicalDocFields .model_dump()
    evidence: list[FieldEvidence]
    validation: ValidationResult


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = ""
    queued_at: datetime | None = None
    completed_at: datetime | None = None
