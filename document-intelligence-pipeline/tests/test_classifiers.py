"""Tests for the document classifier."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.classifiers.document_classifier import DocumentClassifier
from src.models.schemas import DocumentType
from src.extractors.pdf_extractor import PDFExtractor

SAMPLES = Path(__file__).parent.parent / "samples"
clf = DocumentClassifier()


class TestClassifierOnText:
    def test_invoice_text(self):
        text = "Fatura No: FTR-2024-001 KDV oranı %20 toplam tutar 36.000 TL IBAN TR33"
        result = clf.classify(text)
        assert result.document_type == DocumentType.INVOICE
        assert result.confidence > 0.5

    def test_contract_text(self):
        text = "İş bu sözleşme akdedilmiştir. Fesih halinde 30 gün önceden bildirim şarttır. Ceza klozu uygulanır."
        result = clf.classify(text)
        assert result.document_type == DocumentType.CONTRACT

    def test_technical_text(self):
        text = "Teknik doküman versiyon v2.1.0 sistem gereksinimleri kurulum adımları revizyon geçmişi API endpoint"
        result = clf.classify(text)
        assert result.document_type == DocumentType.TECHNICAL

    def test_empty_text_returns_unknown(self):
        result = clf.classify("")
        assert result.document_type == DocumentType.UNKNOWN

    def test_confidence_between_0_and_1(self):
        result = clf.classify("fatura no kdv toplam tutar")
        assert 0.0 <= result.confidence <= 1.0

    def test_scores_sum_to_1(self):
        result = clf.classify("fatura sözleşme teknik")
        total = sum(result.scores.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_uncertain_flag_on_low_confidence(self):
        # Ambiguous text with mixed signals
        result = clf.classify("tarih miktar kalem")
        # uncertain flag should be present when confidence < threshold
        assert isinstance(result.uncertain, bool)


class TestClassifierOnSamplePDFs:
    def _classify_pdf(self, path: Path) -> DocumentType:
        text = PDFExtractor(path).extract().raw_text
        return clf.classify(text).document_type

    def test_invoice_1_classified_correctly(self):
        assert self._classify_pdf(SAMPLES / "invoices" / "sample_invoice_1.pdf") == DocumentType.INVOICE

    def test_invoice_2_classified_correctly(self):
        assert self._classify_pdf(SAMPLES / "invoices" / "sample_invoice_2.pdf") == DocumentType.INVOICE

    def test_contract_1_classified_correctly(self):
        assert self._classify_pdf(SAMPLES / "contracts" / "sample_contract_1.pdf") == DocumentType.CONTRACT

    def test_contract_2_classified_correctly(self):
        assert self._classify_pdf(SAMPLES / "contracts" / "sample_contract_2_nda.pdf") == DocumentType.CONTRACT

    def test_technical_1_classified_correctly(self):
        assert self._classify_pdf(SAMPLES / "technical" / "sample_technical_1_api_doc.pdf") == DocumentType.TECHNICAL

    def test_technical_2_classified_correctly(self):
        assert self._classify_pdf(SAMPLES / "technical" / "sample_technical_2_installation.pdf") == DocumentType.TECHNICAL
