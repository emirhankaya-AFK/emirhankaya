"""Technical document field parser."""
from __future__ import annotations

import re
from src.models.schemas import (
    ExtractionResult, TechnicalDocFields, TechnicalSection, FieldEvidence,
)

_DATE_RE = r"\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4}"

_PATTERNS: dict[str, list[str]] = {
    "baslik": [
        r"^(.{10,120}?)(?:\n|$)",            # first non-empty line often = title
        r"başlık\s*[:\-]?\s*(.{5,120})(?:\n|$)",
        r"doküman\s*adı\s*[:\-]?\s*(.{5,120})(?:\n|$)",
        r"title\s*[:\-]?\s*(.{5,120})(?:\n|$)",
    ],
    "versiyon": [
        r"versiyon\s*[:\-]?\s*(v?\d+[\.\d]*)",
        r"version\s*[:\-]?\s*(v?\d+[\.\d]*)",
        r"revizyon\s*[:\-]?\s*(v?\d+[\.\d]*)",
        r"\b(v\d+\.\d+(?:\.\d+)?)\b",
    ],
    "yazar": [
        r"(?:hazırlayan|yazar|author|prepared\s*by)\s*[:\-]?\s*([A-ZÇĞİÖŞÜ][a-zçğışöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğışöşü]+)+)",
        r"(?:yazan|written\s*by)\s*[:\-]?\s*(.{5,60}?)(?:\n|$)",
    ],
    "tarih": [
        r"(?:tarih|date|düzenleme\s*tarihi)\s*[:\-]?\s*(" + _DATE_RE + r")",
        r"(?:yayın|yayım)\s*tarihi\s*[:\-]?\s*(" + _DATE_RE + r")",
    ],
    "kurulus": [
        r"(?:kuruluş|şirket|organizasyon|firma|department)\s*[:\-]?\s*(.{5,80}?)(?:\n|$)",
        r"(?:hazırlayan\s*birim|prepared\s*by)\s*[:\-]?\s*(.{5,80}?)(?:\n|$)",
    ],
    "ozet": [
        r"(?:özet|abstract|executive\s*summary)\s*[:\-]?\s*(.{20,500}?)(?:\n\n|\Z)",
        r"(?:giriş|introduction)\s*[:\-]?\s*(.{20,500}?)(?:\n\n|\Z)",
    ],
}

# Heading patterns — detect section structure
_HEADING_PATTERNS = [
    r"^(\d+(?:\.\d+)*)\s+([A-ZÇĞİÖŞÜa-zçğışöşü][^\n]{3,80})",  # "1.2 Section Name"
    r"^#{1,4}\s+(.+)$",                                               # Markdown headings
    r"^([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ ]+)$",                               # ALL CAPS headings
]

# Keyword list patterns for extraction
_KEYWORD_PATTERNS = [
    r"(?:anahtar\s*kelimeler|keywords)\s*[:\-]?\s*(.{5,200}?)(?:\n\n|\n[A-Z]|\Z)",
    r"(?:etiketler|tags)\s*[:\-]?\s*(.{5,150}?)(?:\n|$)",
]

_REVISION_PATTERNS = [
    r"(?:revizyon\s*no|rev\.?)\s*[:\-]?\s*(v?\d[\d\.]*)\s*[\|,\-]\s*([^\n]{5,80})",
    r"(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4})\s*[\|,\-]\s*([^\n]{5,80})",
]


class TechnicalDocParser:
    """Extracts structured fields from technical documents."""

    def parse(self, extraction: ExtractionResult) -> tuple[TechnicalDocFields, list[FieldEvidence]]:
        text = extraction.raw_text
        fields = TechnicalDocFields()
        evidence: list[FieldEvidence] = []

        # Standard fields
        for field_name, patterns in _PATTERNS.items():
            value, ev = _extract_first(field_name, patterns, text, extraction)
            if value:
                setattr(fields, field_name, value.strip()[:300])
                if ev:
                    evidence.append(ev)

        # Section structure
        fields.bolumler = self._extract_sections(extraction)

        # Keywords
        fields.anahtar_kelimeler = self._extract_keywords(text)

        # Revision history
        fields.revizyon_gecmisi = self._extract_revisions(text)

        return fields, evidence

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_sections(extraction: ExtractionResult) -> list[TechnicalSection]:
        sections: list[TechnicalSection] = []
        seen: set[str] = set()

        for page in extraction.pages:
            for line in page.text.splitlines():
                line = line.strip()
                if not line or len(line) > 120:
                    continue
                for pattern in _HEADING_PATTERNS:
                    m = re.match(pattern, line, re.UNICODE)
                    if m:
                        title = m.group(2) if m.lastindex >= 2 else m.group(1)
                        title = title.strip()
                        if title and title not in seen:
                            seen.add(title)
                            # Estimate level from numbering depth
                            level = line.count(".") + 1 if re.match(r"^\d", line) else 1
                            sections.append(TechnicalSection(
                                title=title,
                                level=min(level, 4),
                                page=page.page_number,
                            ))
                        break

        return sections[:30]  # cap at 30 sections

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        for pattern in _KEYWORD_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE | re.UNICODE | re.DOTALL)
            if m:
                raw = m.group(1)
                # Split by common delimiters
                kws = re.split(r"[,;\|\/\n]+", raw)
                return [k.strip() for k in kws if 2 < len(k.strip()) < 50][:15]
        return []

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_revisions(text: str) -> list[str]:
        revisions: list[str] = []
        for pattern in _REVISION_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE | re.UNICODE):
                rev_entry = " — ".join(g.strip() for g in m.groups() if g)
                if rev_entry and rev_entry not in revisions:
                    revisions.append(rev_entry)
        return revisions[:10]


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
        m = re.search(pattern, text, re.IGNORECASE | re.UNICODE | re.MULTILINE | re.DOTALL)
        if m:
            value = m.group(1) if m.lastindex else m.group(0)
            value = value.strip()
            if not value or len(value) < 2:
                continue
            page_num, snippet = _locate(m.group(0), extraction)
            return value, FieldEvidence(
                field=field_name,
                value=value,
                page=page_num,
                snippet=snippet,
                confidence=0.85,
                match_pattern=pattern[:60],
            )
    return "", None


def _locate(match_str: str, extraction: ExtractionResult) -> tuple[int, str]:
    probe = match_str[:30].lower()
    for page in extraction.pages:
        idx = page.text.lower().find(probe)
        if idx >= 0:
            start = max(0, idx - 20)
            end = min(len(page.text), idx + 100)
            snippet = "..." + page.text[start:end].replace("\n", " ") + "..."
            return page.page_number, snippet
    return 1, f"...{match_str[:60]}..."
