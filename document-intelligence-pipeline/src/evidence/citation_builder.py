"""Citation builder — attaches page number, snippet, and bbox to each field."""
from __future__ import annotations

from src.models.schemas import ExtractionResult, FieldEvidence


class CitationBuilder:
    """Enriches field evidence with precise page-level citations and bboxes."""

    def __init__(self, extraction: ExtractionResult, bbox_data: list[dict] | None = None):
        """
        Args:
            extraction: Full extraction result (text per page).
            bbox_data: Optional list of {page, text, bbox} from PDFExtractor.get_text_with_bbox().
                       When provided, enables bounding-box attachment per field.
        """
        self.extraction = extraction
        self.bbox_data = bbox_data or []

    # ------------------------------------------------------------------
    def enrich(self, evidence: list[FieldEvidence]) -> list[FieldEvidence]:
        """Return evidence list with page/snippet/bbox filled in from the text."""
        enriched: list[FieldEvidence] = []
        for ev in evidence:
            enriched.append(self._enrich_one(ev))
        return enriched

    # ------------------------------------------------------------------
    def _enrich_one(self, ev: FieldEvidence) -> FieldEvidence:
        value_str = str(ev.value)
        if not value_str:
            return ev

        # Find best page
        best_page, best_snippet = self._find_in_pages(value_str)
        ev = ev.model_copy(update={"page": best_page, "snippet": best_snippet})

        # Attach bbox if available
        if self.bbox_data:
            bbox = self._find_bbox(value_str, best_page)
            if bbox:
                # Store bbox in snippet as structured hint
                ev = ev.model_copy(update={"snippet": ev.snippet + f" [bbox:{bbox}]"})

        return ev

    # ------------------------------------------------------------------
    def _find_in_pages(self, value: str) -> tuple[int, str]:
        """Search for value across pages and return (page_number, context_snippet)."""
        for page in self.extraction.pages:
            idx = page.text.lower().find(value.lower())
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(page.text), idx + len(value) + 40)
                snippet = "..." + page.text[start:end].replace("\n", " ").strip() + "..."
                return page.page_number, snippet

        # Fallback: try partial match (first 10 chars)
        probe = value[:10].lower()
        for page in self.extraction.pages:
            idx = page.text.lower().find(probe)
            if idx >= 0:
                start = max(0, idx - 20)
                end = min(len(page.text), idx + 80)
                snippet = "..." + page.text[start:end].replace("\n", " ").strip() + "..."
                return page.page_number, snippet

        return 1, f"«{value[:60]}»"

    # ------------------------------------------------------------------
    def _find_bbox(self, value: str, target_page: int) -> list[float] | None:
        """Find bounding box from bbox_data for the given value on target_page."""
        probe = value.lower()[:20]
        for block in self.bbox_data:
            if block["page"] == target_page and probe in block["text"].lower():
                return block["bbox"]
        return None

    # ------------------------------------------------------------------
    def build_summary(self, evidence: list[FieldEvidence]) -> dict[str, dict]:
        """Return a page → [field names] mapping for the dashboard."""
        summary: dict[str, list[str]] = {}
        for ev in evidence:
            key = f"Sayfa {ev.page}"
            summary.setdefault(key, []).append(ev.field)
        return {k: {"fields": v, "count": len(v)} for k, v in summary.items()}
