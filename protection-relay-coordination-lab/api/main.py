"""HTTP interface for relay coordination studies."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from relaycoord import (
    CoordinationStudy,
    analyze_study,
    coordinated_feeder,
    miscoordinated_feeder,
)

app = FastAPI(title="Protection Relay Coordination Lab", version="0.1.0")
dashboard_directory = Path(__file__).resolve().parent.parent / "dashboard"
app.mount("/static", StaticFiles(directory=dashboard_directory), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(dashboard_directory / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "scope": "calculation study, not a protection setting approval"}


@app.get("/presets/{name}")
def preset(name: str):
    study = miscoordinated_feeder() if name == "miscoordinated" else coordinated_feeder()
    return {"study": study, "result": analyze_study(study)}


@app.post("/analyze")
def analyze(study: CoordinationStudy):
    return analyze_study(study)
