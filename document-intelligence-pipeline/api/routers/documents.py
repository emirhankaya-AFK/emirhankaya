"""Document upload and status endpoints."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.models.schemas import JobStatus, StatusResponse, UploadResponse

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/doc_uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 20


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF or DOCX for processing.

    Returns a job_id that can be polled via GET /status/{job_id}.
    """
    # Validate extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen format: '{suffix}'. PDF veya DOCX yükleyin.",
        )

    # Read and validate size
    data = await file.read()
    size_mb = len(data) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya çok büyük: {size_mb:.1f} MB. Maksimum {MAX_FILE_SIZE_MB} MB.",
        )

    # Save file
    job_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{job_id}{suffix}"
    save_path.write_bytes(data)

    # Enqueue job
    try:
        from src.pipeline.worker import enqueue_document
        enqueue_document(str(save_path), job_id)
        status = JobStatus.QUEUED
        message = "Dosya kuyruğa alındı. İşlem başlıyor."
    except Exception:
        # Redis unavailable — run synchronously as fallback
        _run_sync(str(save_path), job_id)
        status = JobStatus.DONE
        message = "Dosya işlendi (senkron mod — Redis bağlantısı yok)."

    return UploadResponse(job_id=job_id, status=status, message=message)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Poll job status: queued | processing | done | failed."""
    import json

    try:
        from src.pipeline.worker import get_redis
        r = get_redis()
        raw = r.get(f"status:{job_id}")
        if not raw:
            raise HTTPException(status_code=404, detail=f"Job bulunamadı: {job_id}")
        data = json.loads(raw)
        return StatusResponse(
            job_id=job_id,
            status=JobStatus(data["status"]),
            message=data.get("message", ""),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Redis bağlantısı yok.")


# ---------------------------------------------------------------------------
# Synchronous fallback (when Redis is not available)
# ---------------------------------------------------------------------------

def _run_sync(file_path: str, job_id: str) -> None:
    """Run the pipeline synchronously and store result in a temp JSON file."""
    from src.pipeline.coordinator import DocumentPipeline

    result_dir = Path(os.getenv("RESULT_DIR", "/tmp/doc_results"))
    result_dir.mkdir(parents=True, exist_ok=True)

    try:
        pipeline = DocumentPipeline()
        result = pipeline.run(file_path, job_id=job_id)
        (result_dir / f"{job_id}.json").write_text(result.model_dump_json(), encoding="utf-8")
    except Exception as e:
        (result_dir / f"{job_id}.error").write_text(str(e), encoding="utf-8")
