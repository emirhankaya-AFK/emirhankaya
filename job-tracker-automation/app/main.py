import re
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field, HttpUrl


class Status(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=2, max_length=200)
    url: HttpUrl
    description: str = Field(min_length=20, max_length=30_000)
    source: str = Field(default="manual", max_length=50)
    salary_text: str = Field(default="", max_length=500)


class Job(JobCreate):
    id: str
    status: Status = Status.SAVED
    matched_skills: list[str]
    created_at: datetime
    is_paid: bool
    salary_currency: str | None
    salary_min: float | None
    salary_max: float | None


SKILLS = (
    "python",
    "fastapi",
    "flask",
    "django",
    "sql",
    "postgresql",
    "docker",
    "aws",
    "react",
    "typescript",
    "pytorch",
    "tensorflow",
    "nlp",
    "llm",
    "rag",
    "playwright",
)
jobs: dict[str, Job] = {}


def parse_salary(text: str) -> tuple[bool, str | None, float | None, float | None]:
    lowered = text.lower()
    unpaid_terms = ("volunteer", "unpaid", "equity only", "token only", "project token")
    if any(term in lowered for term in unpaid_terms):
        return False, None, None, None
    currency = next(
        (
            code
            for code, marker in (
                ("USD", "$"),
                ("EUR", "€"),
                ("GBP", "£"),
                ("TRY", "₺"),
            )
            if marker in text or code.lower() in lowered
        ),
        None,
    )
    values = [float(value.replace(",", "")) for value in re.findall(r"\d+(?:[,.]\d+)?", text)]
    if not values or not currency:
        return False, currency, None, None
    return True, currency, min(values), max(values)


def match_skills(description: str, profile: set[str]) -> list[str]:
    lowered = description.lower()
    return [skill for skill in SKILLS if skill in profile and skill in lowered]


def create_app() -> FastAPI:
    app = FastAPI(title="Job Tracker Automation", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "job-tracker-automation"}

    @app.post("/api/v1/jobs", response_model=Job, status_code=201)
    async def add_job(payload: JobCreate) -> Job:
        profile = {
            "python",
            "fastapi",
            "sql",
            "docker",
            "aws",
            "react",
            "typescript",
            "llm",
            "rag",
            "playwright",
        }
        paid, currency, salary_min, salary_max = parse_salary(payload.salary_text)
        job = Job(
            id=str(uuid4()),
            matched_skills=match_skills(payload.description, profile),
            created_at=datetime.now(UTC),
            is_paid=paid,
            salary_currency=currency,
            salary_min=salary_min,
            salary_max=salary_max,
            **payload.model_dump(),
        )
        jobs[job.id] = job
        return job

    @app.patch("/api/v1/jobs/{job_id}/status", response_model=Job)
    async def update_status(job_id: str, status: Status) -> Job:
        job = jobs[job_id]
        updated = job.model_copy(update={"status": status})
        jobs[job_id] = updated
        return updated

    @app.get("/api/v1/jobs", response_model=list[Job])
    async def list_jobs() -> list[Job]:
        return list(jobs.values())

    return app


app = create_app()
