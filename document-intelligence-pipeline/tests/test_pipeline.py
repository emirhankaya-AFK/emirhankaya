"""End-to-end pipeline tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.coordinator import DocumentPipeline
from src.models.schemas import DocumentType

SAMPLES = Path(__file__).parent.parent / "samples"
pipeline = DocumentPipeline()


class TestPipelineE2E:
    def test_invoice_1_full_pipeline(self):
        result = pipeline.run(SAMPLES / "invoices" / "sample_invoice_1.pdf")
        assert result.job_id
        assert result.classification.document_type == DocumentType.INVOICE
        assert len(result.fields) > 0
        assert len(result.evidence) > 0
        assert result.validation is not None

    def test_contract_1_full_pipeline(self):
        result = pipeline.run(SAMPLES / "contracts" / "sample_contract_1.pdf")
        assert result.classification.document_type == DocumentType.CONTRACT
        fields = result.fields
        assert "sozlesme_no" in fields or "taraflar" in fields

    def test_technical_1_full_pipeline(self):
        result = pipeline.run(SAMPLES / "technical" / "sample_technical_1_api_doc.pdf")
        assert result.classification.document_type == DocumentType.TECHNICAL
        assert "versiyon" in result.fields

    def test_result_has_all_sections(self):
        result = pipeline.run(SAMPLES / "invoices" / "sample_invoice_1.pdf")
        assert result.extraction is not None
        assert result.classification is not None
        assert result.evidence is not None
        assert result.validation is not None

    def test_evidence_fields_have_page_and_snippet(self):
        result = pipeline.run(SAMPLES / "invoices" / "sample_invoice_1.pdf")
        for ev in result.evidence:
            assert ev.page >= 1
            assert len(ev.snippet) > 0
            assert 0.0 <= ev.confidence <= 1.0

    def test_incomplete_invoice_validation_catches_issues(self):
        result = pipeline.run(SAMPLES / "invoices" / "sample_invoice_3_incomplete.pdf")
        assert not result.validation.is_valid or len(result.validation.issues) > 0

    def test_pipeline_run_bytes(self):
        pdf_path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        data = pdf_path.read_bytes()
        result = pipeline.run_bytes(data, "sample_invoice_1.pdf")
        assert result.classification.document_type == DocumentType.INVOICE

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Desteklenmeyen"):
            pipeline.run(Path("document.xlsx"))

    def test_all_sample_files_classified(self):
        """All 7 sample files should produce a valid (non-UNKNOWN) classification."""
        sample_files = list(SAMPLES.rglob("*.pdf"))
        assert len(sample_files) >= 7, f"Expected ≥7 sample PDFs, found {len(sample_files)}"

        for pdf in sample_files:
            result = pipeline.run(pdf)
            assert result.classification.document_type != DocumentType.UNKNOWN, (
                f"{pdf.name} classified as UNKNOWN — review lexicon weights"
            )
