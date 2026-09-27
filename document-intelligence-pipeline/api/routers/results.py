"""Results retrieval endpoints."""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

RESULT_DIR = Path(os.getenv("RESULT_DIR", "/tmp/doc_results"))


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    """Retrieve full pipeline result for a completed job."""
    result_data = _load_result(job_id)
    return JSONResponse(content=result_data)


@router.get("/result/{job_id}/fields")
async def get_fields(job_id: str):
    """Retrieve only the extracted fields (compact view)."""
    result_data = _load_result(job_id)
    return JSONResponse(content={
        "job_id": job_id,
        "document_type": result_data.get("classification", {}).get("document_type"),
        "confidence": result_data.get("classification", {}).get("confidence"),
        "fields": result_data.get("fields", {}),
        "validation": result_data.get("validation", {}),
    })


@router.get("/result/{job_id}/evidence")
async def get_evidence(job_id: str):
    """Retrieve field citations with page numbers and snippets."""
    result_data = _load_result(job_id)
    return JSONResponse(content={
        "job_id": job_id,
        "evidence": result_data.get("evidence", []),
    })


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _load_result(job_id: str) -> dict:
    """Load result from Redis or fallback JSON file."""
    # Try Redis first
    try:
        from src.pipeline.worker import get_redis
        r = get_redis()
        raw = r.get(f"result:{job_id}")
        if raw:
            return json.loads(raw)
    except Exception:
        pass

    # Fallback: local JSON file
    result_file = RESULT_DIR / f"{job_id}.json"
    if result_file.exists():
        return json.loads(result_file.read_text(encoding="utf-8"))

    error_file = RESULT_DIR / f"{job_id}.error"
    if error_file.exists():
        raise HTTPException(
            status_code=422,
            detail=f"Pipeline hatası: {error_file.read_text()}",
        )

    raise HTTPException(status_code=404, detail=f"Sonuç bulunamadı: {job_id}")
