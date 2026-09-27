"""RQ worker job definitions."""
from __future__ import annotations

import json
import os

import redis
from rq import Queue

from src.pipeline.coordinator import DocumentPipeline

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_conn: redis.Redis | None = None
_queue: Queue | None = None


def get_redis() -> redis.Redis:
    global _redis_conn
    if _redis_conn is None:
        _redis_conn = redis.from_url(REDIS_URL)
    return _redis_conn


def get_queue() -> Queue:
    global _queue
    if _queue is None:
        _queue = Queue("documents", connection=get_redis())
    return _queue


# ---------------------------------------------------------------------------
# Job functions (executed by RQ worker process)
# ---------------------------------------------------------------------------

def process_document_job(file_path: str, job_id: str) -> dict:
    """Process a document file and store result in Redis.

    This function runs inside the RQ worker. It writes the result JSON
    to Redis with key `result:{job_id}` and sets TTL to 1 hour.
    """
    r = get_redis()

    try:
        pipeline = DocumentPipeline()
        result = pipeline.run(file_path, job_id=job_id)
        result_json = result.model_dump_json()

        r.setex(f"result:{job_id}", 3600, result_json)
        r.setex(f"status:{job_id}", 3600, json.dumps({
            "status": "done",
            "message": "Pipeline tamamlandı.",
        }))

        return {"status": "done", "job_id": job_id}

    except Exception as exc:
        error_msg = str(exc)
        r.setex(f"status:{job_id}", 3600, json.dumps({
            "status": "failed",
            "message": error_msg,
        }))
        raise


def enqueue_document(file_path: str, job_id: str) -> str:
    """Enqueue a document processing job and return RQ job ID."""
    r = get_redis()
    r.setex(f"status:{job_id}", 3600, json.dumps({
        "status": "queued",
        "message": "İşlem kuyruğa alındı.",
    }))

    queue = get_queue()
    queue.enqueue(
        process_document_job,
        file_path,
        job_id,
        job_timeout=120,
        job_id=f"rq_{job_id}",
    )
    return job_id
