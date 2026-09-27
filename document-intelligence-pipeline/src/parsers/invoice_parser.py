"""Turkish invoice field parser using regex pattern matching."""
from __future__ import annotations

import re
from src.models.schemas import ExtractionResult, InvoiceFields, InvoiceLineItem, FieldEvidence


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_PATTERNS: dict[str, list[str]] = {
    "fatura_no": [
        r"fatura\s*no\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"fatura\s*numarası\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"invoice\s*no\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"\bFTR[-\/]?\d+\b",
        r"\bFT[-\/]?\d+\b",
    ],
    "tarih": [
        r"(?:fatura\s*)?tarih[i]?\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
        r"düzenleme\s*tarihi\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
        r"tarih\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
    ],
    "vade_tarihi": [
        r"vade\s*tarihi\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
        r"son\s*ödeme\s*tarihi\s*[:\-]?\s*(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})",
    ],
    "satici_adi": [
        # Strict Turkish (well-formed PDF)
        r"satıcı\s*(?:ünvanı|adı|firma)?\s*[:\-]?\s*([A-ZÇĞİÖŞÜa-zçğışöşü0-9 \.&,]+(?:A\.Ş\.|Ltd\.|AŞ|LTD|ŞTİ\.?))",
        r"(?:firma|şirket)\s*adı\s*[:\-]?\s*(.+?)(?:\n|vergi)",
        # Tolerant: match company on first non-empty lines of document (header area)
        # Handles corrupted Turkish chars like "ÖRNEK T CARET A. ." → keep as-is
        r"^([A-ZÇĞÖÜA-Z][A-ZÇĞİÖŞÜa-zçğışöşü0-9 \.&,\n]{3,50}?(?:A\.(?:Ş|\.)?\.|Ltd\.|nti\.|ŞTİ|AŞ|A\.\s*\.))",
        # Fallback: second line of doc if it looks like a company name
        r"(?:^|\n)([A-ZÇĞÖÜ\s]{3,}(?:A\.\s*[ŞS\.]|Ltd\.|nti\.))",
    ],
    "satici_vkn": [
        r"satıcı\s*(?:vergi\s*kimlik\s*no|vkn)\s*[:\-]?\s*(\d{10,11})",
        r"vergi\s*(?:kimlik\s*)?no\s*[:\-]?\s*(\d{10,11})",
        r"vkn\s*[:\-]?\s*(\d{10,11})",
    ],
    "alici_adi": [
        r"alıcı\s*(?:ünvanı|adı|firma)?\s*[:\-]?\s*([A-ZÇĞİÖŞÜa-zçğışöşü0-9 \.&,]+(?:A\.Ş\.|Ltd\.|AŞ|LTD|ŞTİ\.?))",
        r"müşteri\s*(?:adı|firma)?\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"sayın\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "alici_vkn": [
        r"alıcı\s*(?:vergi\s*kimlik\s*no|vkn)\s*[:\-]?\s*(\d{10,11})",
        r"müşteri\s*(?:vergi\s*kimlik\s*no|vkn)\s*[:\-]?\s*(\d{10,11})",
    ],
    "kdv_orani": [
        r"kdv\s*(?:oranı|%)\s*[:\-]?\s*%?\s*(\d{1,2})",
        r"%\s*(\d{1,2})\s*kdv",
        r"(\d{1,2})\s*%\s*kdv",
    ],
    "kdv_tutari": [
        r"kdv\s*tutarı\s*[:\-]?\s*([\d\.\,]+)\s*(?:TL|TRY|₺)?",
        r"toplam\s*kdv\s*[:\-]?\s*([\d\.\,]+)",
    ],
    "toplam_tutar": [
        # Must match "Genel Toplam" specifically (not Ara Toplam)
        r"genel\s*toplam\s*[:\-]?\s*([\d\.\,]+)\s*(?:TL|TRY|₺|USD|EUR)?",
        r"ödenecek\s*tutar\s*[:\-]?\s*([\d\.\,]+)",
        r"grand\s*total\s*[:\-]?\s*([\d\.\,]+)",
    ],
    "ara_toplam": [
        r"ara\s*toplam\s*[:\-]?\s*([\d\.\,]+)",
        r"subtotal\s*[:\-]?\s*([\d\.\,]+)",
        r"mal\s*hizmet\s*tutarı\s*[:\-]?\s*([\d\.\,]+)",
    ],
    "para_birimi": [
        r"\b(TRY|USD|EUR|GBP|₺)\b",
        r"(?:para\s*birimi|currency)\s*[:\-]?\s*(TRY|USD|EUR|GBP|TL)",
    ],
    "iban": [
        r"iban\s*[:\-]?\s*([A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16})",
        r"\bTR\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}\b",
    ],
    "odeme_kosullari": [
        r"ödeme\s*(?:koşulları|şartları|vadesi)\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"payment\s*terms?\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
}


class InvoiceParser:
    """Extracts structured invoice fields from extraction result."""

    def parse(self, extraction: ExtractionResult) -> tuple[InvoiceFields, list[FieldEvidence]]:
        text = extraction.raw_text
        fields = InvoiceFields()
        evidence: list[FieldEvidence] = []

        for field_name, patterns in _PATTERNS.items():
            value, ev = self._extract_field(field_name, patterns, text, extraction)
            if value:
                setattr(fields, field_name, value)
                if ev:
                    evidence.append(ev)

        # Extract line items from tables
        for page in extraction.pages:
            for table in page.tables:
                items = self._parse_line_items(table)
                if items:
                    fields.kalemler = items
                    break

        return fields, evidence

    # ------------------------------------------------------------------
    def _extract_field(
        self,
        field_name: str,
        patterns: list[str],
        text: str,
        extraction: ExtractionResult,
    ) -> tuple[str, FieldEvidence | None]:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if match:
                # Take first capture group or full match
                value = match.group(1) if match.lastindex else match.group(0)
                value = value.strip()
                if not value:
                    continue

                # Find which page contains the match
                page_num, snippet = self._locate_in_pages(match.group(0), extraction)
                ev = FieldEvidence(
                    field=field_name,
                    value=value,
                    page=page_num,
                    snippet=snippet,
                    confidence=0.90,
                    match_pattern=pattern[:60],
                )
                return value, ev

        return "", None

    # ------------------------------------------------------------------
    @staticmethod
    def _locate_in_pages(match_str: str, extraction: ExtractionResult) -> tuple[int, str]:
        for page in extraction.pages:
            idx = page.text.lower().find(match_str.lower())
            if idx >= 0:
                start = max(0, idx - 30)
                end = min(len(page.text), idx + len(match_str) + 30)
                snippet = "..." + page.text[start:end].replace("\n", " ") + "..."
                return page.page_number, snippet
        return 1, f"...{match_str}..."

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_line_items(table: list[list[str]]) -> list[InvoiceLineItem]:
        """Detect invoice line items from a table."""
        if not table or len(table) < 2:
            return []

        header = [h.lower() for h in table[0]]
        desc_idx = _find_col(header, ["açıklama", "mal/hizmet", "ürün", "kalem", "hizmet adı", "description"])
        qty_idx  = _find_col(header, ["miktar", "adet", "qty", "quantity"])
        price_idx = _find_col(header, ["birim fiyat", "fiyat", "price", "unit price"])
        total_idx = _find_col(header, ["tutar", "toplam", "amount", "total"])

        if desc_idx is None:
            return []

        items: list[InvoiceLineItem] = []
        for row in table[1:]:
            if not row or all(c.strip() == "" for c in row):
                continue
            item = InvoiceLineItem(
                description=row[desc_idx].strip() if desc_idx < len(row) else "",
                quantity=row[qty_idx].strip() if qty_idx is not None and qty_idx < len(row) else "",
                unit_price=row[price_idx].strip() if price_idx is not None and price_idx < len(row) else "",
                total=row[total_idx].strip() if total_idx is not None and total_idx < len(row) else "",
            )
            if item.description:
                items.append(item)

        return items


def _find_col(header: list[str], candidates: list[str]) -> int | None:
    for i, h in enumerate(header):
        for cand in candidates:
            if cand in h:
                return i
    return None
