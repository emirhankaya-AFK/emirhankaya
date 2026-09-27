# Job Tracker & Automation

[English](README.md) | [Türkçe](README_TR.md) | [Deutsch](README_DE.md)

A production-shaped job tracking API. Save a listing, explain which skills match a profile, and move it through saved, applied, interview or rejected states.

![Demo](docs/demo.svg)

## Stack
Python, FastAPI, Pydantic, Playwright-ready ingestion boundary, SQLite/PostgreSQL-ready persistence boundary, Docker, pytest and GitHub Actions. The MVP keeps records in memory for deterministic tests; the next adapter persists jobs and schedules Playwright collectors with retries.

## API and run
- POST /api/v1/jobs saves a listing and returns matched skills.
- PATCH /api/v1/jobs/{id}/status?status=applied updates its workflow state.
- GET /api/v1/jobs lists the dashboard feed.

Salary screening is explicit: salary_text is parsed into currency and a numeric range. Listings marked volunteer, unpaid, equity-only, token-only or project-token are returned with is_paid=false so they can be excluded before applying.

Example request:

    {"title":"Backend Engineer","company":"Acme","url":"https://example.com/1","description":"Python FastAPI","salary_text":"$60,000-$70,000 USD"}

    pip install -e ".[dev]"
    uvicorn app.main:app --reload
    pytest -q

Docker: docker compose up --build. Interactive docs: /docs.

Only genuine salary fields should be accepted by a future collector; token-only, volunteer and unpaid listings must be filtered out.
