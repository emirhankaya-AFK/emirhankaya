"""Tests for PDF and DOCX extractors."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.table_extractor import normalize_table, flatten_table_to_text, extract_numeric

SAMPLES = Path(__file__).parent.parent / "samples"


# ---------------------------------------------------------------------------
# PDF Extractor
# ---------------------------------------------------------------------------

class TestPDFExtractor:
    def test_invoice_extracts_text(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        result = PDFExtractor(path).extract()
        assert result.total_pages >= 1
        assert len(result.raw_text) > 100
        assert result.source_file == str(path)

    def test_invoice_raw_text_contains_key_fields(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        result = PDFExtractor(path).extract()
        text = result.raw_text
        assert "FTR-2024-001234" in text, "Fatura no bulunamadı"
        assert "36.000" in text or "36000" in text, "Toplam tutar bulunamadı"

    def test_contract_extracts_text(self):
        path = SAMPLES / "contracts" / "sample_contract_1.pdf"
        result = PDFExtractor(path).extract()
        assert result.total_pages >= 1
        # "sözleşme" may appear as "sözlenme" due to reportlab font encoding
        assert "söz" in result.raw_text.lower() or "sozle" in result.raw_text.lower()

    def test_technical_extracts_text(self):
        path = SAMPLES / "technical" / "sample_technical_1_api_doc.pdf"
        result = PDFExtractor(path).extract()
        assert "teknik" in result.raw_text.lower()

    def test_pages_have_text(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        result = PDFExtractor(path).extract()
        assert all(isinstance(p.text, str) for p in result.pages)

    def test_bbox_extraction(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        blocks = PDFExtractor(path).get_text_with_bbox()
        assert len(blocks) > 0
        assert all("page" in b and "text" in b and "bbox" in b for b in blocks)
        assert all(len(b["bbox"]) == 4 for b in blocks)


# ---------------------------------------------------------------------------
# Table Extractor utilities
# ---------------------------------------------------------------------------

class TestTableExtractor:
    def test_normalize_table_basic(self):
        raw = [
            ["Ad", "Miktar", "Tutar"],
            ["Kalem A", "2", "100,00"],
            ["Kalem B", "1", "50,00"],
        ]
        records = normalize_table(raw)
        assert len(records) == 2
        assert records[0]["Ad"] == "Kalem A"
        assert records[1]["Tutar"] == "50,00"

    def test_normalize_table_empty_rows_skipped(self):
        raw = [
            ["Ad", "Tutar"],
            ["", ""],
            ["Kalem A", "100"],
        ]
        records = normalize_table(raw)
        assert len(records) == 1

    def test_normalize_table_too_short(self):
        assert normalize_table([]) == []
        assert normalize_table([["Ad"]]) == []

    def test_flatten_table_to_text(self):
        raw = [["A", "B"], ["1", "2"]]
        text = flatten_table_to_text(raw)
        assert "A" in text and "B" in text and "1" in text

    def test_extract_numeric_turkish_format(self):
        assert extract_numeric("1.234,56") == pytest.approx(1234.56)
        assert extract_numeric("36.000,00") == pytest.approx(36000.0)

    def test_extract_numeric_plain(self):
        assert extract_numeric("1234.56") == pytest.approx(1234.56)

    def test_extract_numeric_empty(self):
        assert extract_numeric("") is None
        assert extract_numeric(None) is None
