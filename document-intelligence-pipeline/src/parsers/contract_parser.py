"""Turkish contract field parser."""
from __future__ import annotations

import re
from src.models.schemas import (
    ExtractionResult, ContractFields, ContractParty, FieldEvidence,
)

_DATE_RE = r"\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4}"
_PARTY_CORP = r"[A-ZÇĞİÖŞÜa-zçğışöşü0-9 \.&,]+(?:A\.Ş\.|Ltd\.|AŞ|LTD|ŞTİ\.?|Şirketi|anonim)"

_PATTERNS: dict[str, list[str]] = {
    "sozlesme_no": [
        r"söz(?:le[şs]me|lenme)\s*no\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"sözleşme\s*numarası\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"söz.{0,6}me\s*no\s*[:\-]?\s*([A-Z0-9\-\/]+)",   # tolerant
        r"kontrat\s*no\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        # Matches label that starts a line followed by alphanumeric code
        r"(?:^|\n)\s*söz[^\n]{0,12}no\s*[:\-]?\s*([A-Z0-9\-\/]{4,20})",
    ],
    "sozlesme_turu": [
        r"(hizmet\s*sözleşmesi)",
        r"(iş\s*sözleşmesi)",
        r"(kira\s*sözleşmesi)",
        r"(alım\s*satım\s*sözleşmesi)",
        r"(tedarik\s*sözleşmesi)",
        r"(gizlilik\s*sözleşmesi|nda)",
        r"(proje\s*sözleşmesi)",
        r"(danışmanlık\s*sözleşmesi)",
    ],
    "baslangic_tarihi": [
        r"başlangıç\s*tarihi\s*[:\-]?\s*(" + _DATE_RE + r")",
        r"sözleşme\s*başlangıç\s*[:\-]?\s*(" + _DATE_RE + r")",
        r"(?:tarihinden|tarihinde)\s+itibaren.*?(" + _DATE_RE + r")",
        r"(\b\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4}\b).*?tarihinden\s+itibaren",
    ],
    "bitis_tarihi": [
        r"bitiş\s*tarihi\s*[:\-]?\s*(" + _DATE_RE + r")",
        r"sona\s*erme\s*tarihi\s*[:\-]?\s*(" + _DATE_RE + r")",
        r"geçerlilik\s*süresi.*?(" + _DATE_RE + r")",
    ],
    "sure": [
        r"süre\s*[:\-]?\s*(\d+\s*(?:ay|yıl|gün|hafta))",
        r"(\d+)\s*(?:aylık|yıllık|günlük)\s*sözleşme",
        r"sözleşme\s*süresi\s*[:\-]?\s*(.+?)(?:\n|$)",
    ],
    "odeme_kosullari": [
        r"ödeme\s*(?:koşulları|şartları|planı)\s*[:\-]?\s*(.{10,100}?)(?:\n|madde|$)",
        r"ödeme\s*(?:yöntemi|şekli)\s*[:\-]?\s*(.{5,80}?)(?:\n|$)",
        r"(\d+)\s*gün\s*(?:içinde|vadeli|net)\s*ödeme",
    ],
    "ceza_klozu": [
        r"ceza\s*(?:klozu|maddesi|tutarı)\s*[:\-]?\s*(.{10,150}?)(?:\n|$)",
        r"gecikme\s*(?:faizi|cezası)\s*[:\-]?\s*(.{10,100}?)(?:\n|$)",
        r"tazminat\s*[:\-]?\s*(.{10,100}?)(?:\n|$)",
    ],
    "gizlilik_maddesi": [
        r"(gizlilik|sır\s*saklama)\s*yükümlülüğü.{0,200}?(?:ay|yıl|gün)",
        r"gizli\s*bilgi.{0,100}?(?:ifşa|paylaşım)",
    ],
    "imza_tarihi": [
        r"(?:imza|tanzim)\s*tarihi\s*[:\-]?\s*(" + _DATE_RE + r")",
        r"tarihinde\s+imzalanmıştır",
        r"(\b\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{4}\b).*?imzalanmıştır",
    ],
}

# Fesih patterns — collected separately because multiple matches needed
_FESIH_PATTERNS = [
    r"(fesih\s*(?:halinde|durumunda|bildirim)[^.]{0,150}\.)",
    r"(taraflardan\s*(?:biri|herhangi\s*biri)[^.]{0,120}fesih[^.]{0,120}\.)",
    r"(sözleşme\s*feshedilebilir[^.]{0,120}\.)",
    r"(\d+\s*gün\s*önceden[^.]{0,80}fesih[^.]{0,80}\.)",
]

# Party extraction patterns
_PARTY_PATTERNS = [
    (r"(?:işveren|birinci\s*taraf|1\.\s*taraf)\s*[:\-]?\s*(" + _PARTY_CORP + r")", "İşveren"),
    (r"(?:yüklenici|ikinci\s*taraf|2\.\s*taraf|hizmet\s*sağlayıcı)\s*[:\-]?\s*(" + _PARTY_CORP + r")", "Yüklenici"),
    (r"(?:kiracı|kiralayan|satıcı|alıcı)\s*[:\-]?\s*(" + _PARTY_CORP + r")", "Diğer Taraf"),
]


class ContractParser:
    """Extracts structured contract fields from extraction result."""

    def parse(self, extraction: ExtractionResult) -> tuple[ContractFields, list[FieldEvidence]]:
        text = extraction.raw_text
        fields = ContractFields()
        evidence: list[FieldEvidence] = []

        # Standard single-value fields
        for field_name, patterns in _PATTERNS.items():
            value, ev = _extract_first(field_name, patterns, text, extraction)
            if value:
                setattr(fields, field_name, value.strip())
                if ev:
                    evidence.append(ev)

        # Fesih şartları (multi-match)
        fesih_clauses: list[str] = []
        for pattern in _FESIH_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE | re.UNICODE):
                clause = m.group(1).strip()
                if clause and clause not in fesih_clauses:
                    fesih_clauses.append(clause[:200])
        fields.fesih_sartlari = fesih_clauses[:5]

        # Taraflar
        parties: list[ContractParty] = []
        for pattern, role in _PARTY_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
            if m:
                parties.append(ContractParty(name=m.group(1).strip(), role=role))
        fields.taraflar = parties

        # İmzalayanlar (names after "imzalayan" / signature line)
        signer_matches = re.findall(
            r"(?:imzalayan|yetkili)\s*[:\-]?\s*([A-ZÇĞİÖŞÜ][a-zçğışöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğışöşü]+)",
            text, re.UNICODE,
        )
        fields.imzalayanlar = list(dict.fromkeys(signer_matches))[:4]

        return fields, evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_first(
    field_name: str,
    patterns: list[str],
    text: str,
    extraction: ExtractionResult,
) -> tuple[str, FieldEvidence | None]:
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.UNICODE | re.DOTALL)
        if m:
            value = m.group(1) if m.lastindex else m.group(0)
            value = value.strip()
            if not value:
                continue
            page_num, snippet = _locate(m.group(0), extraction)
            ev = FieldEvidence(
                field=field_name,
                value=value,
                page=page_num,
                snippet=snippet,
                confidence=0.88,
                match_pattern=pattern[:60],
            )
            return value, ev
    return "", None


def _locate(match_str: str, extraction: ExtractionResult) -> tuple[int, str]:
    for page in extraction.pages:
        idx = page.text.lower().find(match_str.lower()[:30])
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(page.text), idx + 100)
            snippet = "..." + page.text[start:end].replace("\n", " ") + "..."
            return page.page_number, snippet
    return 1, f"...{match_str[:60]}..."
