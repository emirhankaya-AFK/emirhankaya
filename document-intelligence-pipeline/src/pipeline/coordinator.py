"""Pipeline coordinator — orchestrates extract → classify → parse → validate → cite."""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.docx_extractor import DocxExtractor
from src.classifiers.document_classifier import DocumentClassifier
from src.parsers.invoice_parser import InvoiceParser
from src.parsers.contract_parser import ContractParser
from src.parsers.technical_parser import TechnicalDocParser
from src.evidence.citation_builder import CitationBuilder
from src.validation.field_validator import FieldValidator
from src.models.schemas import (
    DocumentType,
    ExtractionResult,
    PipelineResult,
    InvoiceFields,
    ContractFields,
    TechnicalDocFields,
)


class DocumentPipeline:
    """Runs the full document intelligence pipeline on a file or raw bytes."""

    def __init__(self):
        self.classifier = DocumentClassifier()
        self.invoice_parser = InvoiceParser()
        self.contract_parser = ContractParser()
        self.technical_parser = TechnicalDocParser()
        self.validator = FieldValidator()

    # ------------------------------------------------------------------
    def run(self, file_path: str | Path, job_id: str | None = None) -> PipelineResult:
        """Run pipeline on a file path. Returns PipelineResult."""
        file_path = Path(file_path)
        job_id = job_id or str(uuid.uuid4())

        # Step 1: Extract
        extraction = self._extract(file_path)

        # Step 2: Classify
        classification = self.classifier.classify(extraction.raw_text)

        # Step 3: Parse fields
        fields, raw_evidence = self._parse(classification.document_type, extraction)

        # Step 4: Enrich citations
        bbox_data: list[dict] = []
        if file_path.suffix.lower() == ".pdf":
            try:
                bbox_data = PDFExtractor(file_path).get_text_with_bbox()
            except Exception:
                pass  # bbox enrichment is optional

        citation_builder = CitationBuilder(extraction, bbox_data)
        evidence = citation_builder.enrich(raw_evidence)

        # Step 5: Validate
        validation = self.validator.validate(classification.document_type, fields)

        return PipelineResult(
            job_id=job_id,
            source_file=str(file_path),
            processed_at=datetime.utcnow(),
            extraction=extraction,
            classification=classification,
            fields=fields.model_dump(),
            evidence=evidence,
            validation=validation,
        )

    # ------------------------------------------------------------------
    def run_bytes(
        self,
        data: bytes,
        filename: str,
        job_id: str | None = None,
    ) -> PipelineResult:
        """Run pipeline on in-memory bytes (PDF only for now)."""
        import tempfile
        import os

        suffix = Path(filename).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)

        try:
            result = self.run(tmp_path, job_id=job_id)
            result = result.model_copy(update={"source_file": filename})
            return result
        finally:
            os.unlink(tmp_path)

    # ------------------------------------------------------------------
    @staticmethod
    def _extract(file_path: Path) -> ExtractionResult:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return PDFExtractor(file_path).extract()
        elif suffix in (".docx", ".doc"):
            return DocxExtractor(file_path).extract()
        else:
            raise ValueError(f"Desteklenmeyen dosya formatı: {suffix}. PDF veya DOCX olmalı.")

    # ------------------------------------------------------------------
    def _parse(
        self,
        doc_type: DocumentType,
        extraction: ExtractionResult,
    ) -> tuple[InvoiceFields | ContractFields | TechnicalDocFields, list]:
        if doc_type == DocumentType.INVOICE:
            return self.invoice_parser.parse(extraction)
        elif doc_type == DocumentType.CONTRACT:
            return self.contract_parser.parse(extraction)
        elif doc_type == DocumentType.TECHNICAL:
            return self.technical_parser.parse(extraction)
        else:
            # Unknown type — return empty invoice fields as fallback
            return InvoiceFields(), []
