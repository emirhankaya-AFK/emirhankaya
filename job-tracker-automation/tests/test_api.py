from fastapi.testclient import TestClient

from app.main import create_app, match_skills, parse_salary


def test_skill_matching_is_explainable() -> None:
    assert match_skills("Python FastAPI and Docker", {"python", "fastapi"}) == ["python", "fastapi"]


def test_salary_parser_rejects_token_only_and_reads_real_money() -> None:
    assert parse_salary("$60,000-$70,000 USD") == (True, "USD", 60_000, 70_000)
    assert parse_salary("$60k plus project token only")[0] is False


def test_job_lifecycle() -> None:
    with TestClient(create_app()) as client:
        created = client.post(
            "/api/v1/jobs",
            json={
                "title": "Backend Engineer",
                "company": "Acme",
                "url": "https://example.com/jobs/1",
                "description": "Build Python FastAPI services with PostgreSQL and Docker.",
                "salary_text": "$60,000-$70,000 USD",
            },
        )
        assert created.status_code == 201
        assert created.json()["is_paid"] is True
        job_id = created.json()["id"]
        updated = client.patch(f"/api/v1/jobs/{job_id}/status?status=applied")
    assert updated.json()["status"] == "applied"
