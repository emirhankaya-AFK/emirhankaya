"""Field validator — detects missing, conflicting, and malformed fields."""
from __future__ import annotations

import re
from src.models.schemas import (
    DocumentType,
    InvoiceFields,
    ContractFields,
    TechnicalDocFields,
    ValidationResult,
    ValidationIssue,
)
from src.extractors.table_extractor import extract_numeric

# ---------------------------------------------------------------------------
# Required fields per document type
# ---------------------------------------------------------------------------

_REQUIRED: dict[DocumentType, list[str]] = {
    DocumentType.INVOICE: ["fatura_no", "tarih", "satici_adi", "toplam_tutar"],
    DocumentType.CONTRACT: ["sozlesme_no", "taraflar", "baslangic_tarihi"],
    DocumentType.TECHNICAL: ["baslik", "versiyon"],
}

# Fields that should follow a specific format
_FORMATS: dict[str, tuple[str, str]] = {
    "satici_vkn":  (r"^\d{10}$", "VKN 10 haneli rakam olmalı"),
    "alici_vkn":   (r"^\d{10}$", "VKN 10 haneli rakam olmalı"),
    "iban": (
        r"^TR\d{2}\d{4}\d{4}\d{4}\d{4}\d{4}\d{2}$",
        "IBAN TR formatında olmalı (TR + 24 rakam)"
    ),
    "kdv_orani":   (r"^\d{1,2}$", "KDV oranı 1-2 haneli rakam olmalı (%0, %8, %18, %20)"),
    "fatura_no":   (r"^[A-Z0-9\-\/]{3,30}$", "Fatura no alfanümerik olmalı"),
    "sozlesme_no": (r"^[A-Z0-9\-\/]{3,30}$", "Sözleşme no alfanümerik olmalı"),
    "versiyon":    (r"^v?\d+(\.\d+)*$", "Versiyon formatı 'v1.2.3' olmalı"),
}


class FieldValidator:
    """Validates extracted fields for completeness and consistency."""

    def validate(
        self,
        doc_type: DocumentType,
        fields: InvoiceFields | ContractFields | TechnicalDocFields,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        missing: list[str] = []
        conflicts: list[str] = []
        format_errors: list[str] = []

        fields_dict = fields.model_dump()

        # 1. Required field check
        for req_field in _REQUIRED.get(doc_type, []):
            value = fields_dict.get(req_field)
            is_missing = (
                value is None
                or value == ""
                or value == []
                or value == {}
            )
            if is_missing:
                missing.append(req_field)
                issues.append(ValidationIssue(
                    issue_type="missing",
                    field=req_field,
                    message=f"Zorunlu alan bulunamadı: '{req_field}'",
                    severity="error",
                ))

        # 2. Format checks
        for field_name, (pattern, msg) in _FORMATS.items():
            value = fields_dict.get(field_name, "")
            if value and isinstance(value, str) and value.strip():
                cleaned = re.sub(r"\s", "", value)
                if not re.match(pattern, cleaned, re.IGNORECASE):
                    format_errors.append(field_name)
                    issues.append(ValidationIssue(
                        issue_type="format_error",
                        field=field_name,
                        message=f"Format hatası — {msg}. Bulunan değer: '{value[:50]}'",
                        severity="warning",
                    ))

        # 3. Numeric consistency checks (invoice only)
        if doc_type == DocumentType.INVOICE and isinstance(fields, InvoiceFields):
            conflict_msgs = self._check_invoice_math(fields)
            for msg in conflict_msgs:
                conflicts.append("invoice_math")
                issues.append(ValidationIssue(
                    issue_type="conflict",
                    field="toplam_tutar",
                    message=msg,
                    severity="warning",
                ))

        # 4. Date logic checks
        date_conflicts = _check_date_order(
            fields_dict.get("baslangic_tarihi", ""),
            fields_dict.get("bitis_tarihi", ""),
        )
        for msg in date_conflicts:
            conflicts.append("date_order")
            issues.append(ValidationIssue(
                issue_type="conflict",
                field="bitis_tarihi",
                message=msg,
                severity="warning",
            ))

        is_valid = not any(i.severity == "error" for i in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            missing_fields=missing,
            conflicts=conflicts,
            format_errors=format_errors,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _check_invoice_math(fields: InvoiceFields) -> list[str]:
        """Check: ara_toplam × (1 + kdv_oran) ≈ toplam_tutar."""
        conflicts: list[str] = []

        ara = extract_numeric(fields.ara_toplam)
        kdv = extract_numeric(fields.kdv_orani)
        kdv_tutar = extract_numeric(fields.kdv_tutari)
        toplam = extract_numeric(fields.toplam_tutar)

        if ara and kdv and toplam:
            expected = round(ara * (1 + kdv / 100), 2)
            if abs(expected - toplam) > 1.0:  # 1 TL tolerance
                conflicts.append(
                    f"Toplam tutar çelişkisi: ara_toplam({ara}) × (1+{kdv}%) = {expected:.2f}, "
                    f"belgede {toplam}"
                )

        if ara and kdv_tutar and toplam:
            expected2 = round(ara + kdv_tutar, 2)
            if abs(expected2 - toplam) > 1.0:
                conflicts.append(
                    f"Toplam tutar çelişkisi: ara_toplam({ara}) + kdv({kdv_tutar}) = {expected2:.2f}, "
                    f"belgede {toplam}"
                )

        return conflicts


def _check_date_order(start: str, end: str) -> list[str]:
    """Naively compare date strings — if end < start, flag."""
    if not start or not end:
        return []
    try:
        # Normalize to YYYY-MM-DD for comparison
        s = _normalize_date(start)
        e = _normalize_date(end)
        if s and e and e < s:
            return [f"Bitiş tarihi ({end}) başlangıç tarihinden ({start}) önce."]
    except Exception:
        pass
    return []


def _normalize_date(date_str: str) -> str | None:
    """Try to convert DD.MM.YYYY or DD/MM/YYYY → YYYY-MM-DD."""
    m = re.match(r"(\d{1,2})[\/\.\-](\d{1,2})[\/\.\-](\d{2,4})", date_str)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return None
