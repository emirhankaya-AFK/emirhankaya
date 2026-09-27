"""Table normalization utilities."""
from __future__ import annotations

import re


def normalize_table(raw: list[list[str]]) -> list[dict[str, str]]:
    """Convert raw table (list of rows) into list of dicts using first row as header.

    Example:
        [["Ad", "Miktar"], ["Kalem A", "100"]]
        → [{"Ad": "Kalem A", "Miktar": "100"}]
    """
    if not raw or len(raw) < 2:
        return []

    headers = [_clean(h) for h in raw[0]]
    records: list[dict[str, str]] = []

    for row in raw[1:]:
        if all(cell.strip() == "" for cell in row):
            continue  # skip empty rows
        padded = row + [""] * (len(headers) - len(row))
        record = {headers[i]: _clean(padded[i]) for i in range(len(headers))}
        records.append(record)

    return records


def flatten_table_to_text(raw: list[list[str]]) -> str:
    """Render a table as plain text for keyword matching."""
    lines: list[str] = []
    for row in raw:
        lines.append(" | ".join(cell.strip() for cell in row))
    return "\n".join(lines)


def extract_numeric(value: str) -> float | None:
    """Parse a number string to float, handling both Turkish and plain decimal formats.

    Turkish format: '1.234,56' (dot=thousands sep, comma=decimal) → 1234.56
    Plain decimal:  '1234.56' (dot=decimal) → 1234.56
    """
    if not value:
        return None
    s = re.sub(r"[^\d.,]", "", value.strip())
    if not s:
        return None

    # Comma present → Turkish format (dots are thousands separators)
    if "," in s:
        try:
            return float(s.replace(".", "").replace(",", "."))
        except ValueError:
            return None

    # No comma — detect by fractional digit count
    parts = s.split(".")
    if len(parts) == 2 and len(parts[1]) <= 2:
        # 1–2 fractional digits → plain decimal (e.g. 1234.56)
        try:
            return float(s)
        except ValueError:
            return None

    # Otherwise dot = thousands separator (e.g. 36.000 → 36000)
    try:
        return float(s.replace(".", ""))
    except ValueError:
        return None


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
