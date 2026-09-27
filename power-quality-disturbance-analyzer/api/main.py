"""FastAPI interface and lightweight dashboard for power-quality analysis."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from power_quality import DisturbanceType, PowerQualityAnalyzer, SignalSimulator, SignalWindow

app = FastAPI(
    title="Power Quality Disturbance Analyzer",
    version="0.1.0",
    description="Educational three-phase waveform analysis; not a compliance instrument.",
)
analyzer = PowerQualityAnalyzer()
dashboard_directory = Path(__file__).resolve().parent.parent / "dashboard"
app.mount("/static", StaticFiles(directory=dashboard_directory), name="static")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(dashboard_directory / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "scope": "educational prototype"}


@app.post("/analyze")
def analyze(window: SignalWindow):
    return analyzer.analyze(window)


@app.get("/demo/{disturbance}")
def demo(disturbance: DisturbanceType):
    window = SignalSimulator(seed=42).generate(disturbance)
    return analyzer.analyze(window)


@app.get("/demo/{disturbance}/waveform")
def demo_waveform(disturbance: DisturbanceType) -> dict:
    window = SignalSimulator(seed=42).generate(disturbance)
    result = analyzer.analyze(window)
    step = max(1, len(window.voltage_a) // 800)
    sample_indices = range(0, len(window.voltage_a), step)
    return {
        "time_s": [round(index / window.sample_rate_hz, 6) for index in sample_indices],
        "voltage_a": window.voltage_a[::step],
        "voltage_b": window.voltage_b[::step],
        "voltage_c": window.voltage_c[::step],
        "result": result,
    }
