"""FastAPI endpoint tests using TestClient (no running server needed)."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app

SAMPLES = Path(__file__).parent.parent / "samples"
client = TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_has_version(self):
        response = client.get("/health")
        assert "version" in response.json()


class TestUploadEndpoint:
    def _upload(self, path: Path):
        with open(path, "rb") as f:
            return client.post(
                "/api/v1/upload",
                files={"file": (path.name, f, "application/pdf")},
            )

    def test_upload_pdf_returns_job_id(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        response = self._upload(path)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert len(data["job_id"]) > 10  # UUID

    def test_upload_pdf_status_queued_or_done(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        response = self._upload(path)
        assert response.status_code == 200
        status = response.json()["status"]
        assert status in ("queued", "done")

    def test_upload_wrong_extension_rejected(self):
        # Create a tiny fake file with .txt extension
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"hello")
            tmp_path = tmp.name
        try:
            with open(tmp_path, "rb") as f:
                response = client.post(
                    "/api/v1/upload",
                    files={"file": ("test.txt", f, "text/plain")},
                )
            assert response.status_code == 400
        finally:
            os.unlink(tmp_path)

    def test_result_available_after_sync_upload(self):
        """After upload in sync mode, result should be retrievable."""
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        upload_resp = self._upload(path)
        assert upload_resp.status_code == 200
        job_id = upload_resp.json()["job_id"]
        status = upload_resp.json()["status"]

        if status == "done":
            result_resp = client.get(f"/api/v1/result/{job_id}")
            assert result_resp.status_code == 200
            result = result_resp.json()
            assert "classification" in result
            assert "fields" in result

    def test_fields_endpoint_returns_compact_view(self):
        path = SAMPLES / "contracts" / "sample_contract_1.pdf"
        upload_resp = self._upload(path)
        assert upload_resp.status_code == 200
        job_id = upload_resp.json()["job_id"]
        status = upload_resp.json()["status"]

        if status == "done":
            resp = client.get(f"/api/v1/result/{job_id}/fields")
            assert resp.status_code == 200
            data = resp.json()
            assert "document_type" in data
            assert "fields" in data

    def test_evidence_endpoint(self):
        path = SAMPLES / "invoices" / "sample_invoice_1.pdf"
        upload_resp = self._upload(path)
        job_id = upload_resp.json()["job_id"]
        status = upload_resp.json()["status"]

        if status == "done":
            resp = client.get(f"/api/v1/result/{job_id}/evidence")
            assert resp.status_code == 200
            data = resp.json()
            assert "evidence" in data
            assert isinstance(data["evidence"], list)

    def test_unknown_job_id_returns_404(self):
        resp = client.get("/api/v1/result/nonexistent-job-id-12345")
        assert resp.status_code in (404, 503)
