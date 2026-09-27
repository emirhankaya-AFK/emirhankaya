"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import documents, results

APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify Redis connection
    try:
        from src.pipeline.worker import get_redis
        get_redis().ping()
        print("✅ Redis bağlantısı başarılı.")
    except Exception as e:
        print(f"⚠️  Redis bağlantısı kurulamadı: {e}. Worker özellikleri devre dışı.")
    yield
    # Shutdown (no cleanup needed)


app = FastAPI(
    title="Document Intelligence Pipeline API",
    description=(
        "Turkish Invoice, Contract & Technical Document intelligence platform. "
        "Extract structured fields, citations, and validation reports from PDF/DOCX."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)

# Allow Streamlit dashboard to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(results.router, prefix="/api/v1", tags=["Results"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": APP_VERSION}
