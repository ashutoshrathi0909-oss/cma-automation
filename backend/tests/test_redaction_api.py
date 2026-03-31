"""
Redaction API tests — POST /{id}/detect-names, preview-redaction, apply-redaction.

All tests mock Supabase Storage and DB; pymupdf processing is real.
"""

import pymupdf
import pytest
from unittest.mock import MagicMock, patch


DOC_ID = "doc-uuid-redact-0001"
CLIENT_ID = "client-uuid-0001"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _create_test_pdf(company_name: str = "ABC Industries Private Limited", pages: int = 2) -> bytes:
    """Create a test PDF with a company name in large-font header."""
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 50), company_name, fontsize=18)
        page.insert_text((72, 100), f"Financial Statement Page {i+1}", fontsize=12)
        page.insert_text((72, 130), "Revenue: Rs 45,23,456", fontsize=11)
        page.insert_text((72, 160), f"Prepared for {company_name}", fontsize=11)
    output = doc.tobytes()
    doc.close()
    return output


def _make_query_mock():
    """Self-chaining query builder mock."""
    q = MagicMock()
    for method in ("select", "insert", "update", "delete", "eq", "neq", "ilike", "order", "single", "limit"):
        getattr(q, method).return_value = q
    return q


def _make_storage_mock(download_bytes: bytes = b""):
    bucket = MagicMock()
    bucket.download.return_value = download_bytes
    bucket.upload.return_value = MagicMock()
    bucket.remove.return_value = MagicMock()
    return bucket


def _mock_service(doc_data, pdf_bytes: bytes = b""):
    """Single-result mock returning doc_data on every execute()."""
    svc = MagicMock()
    result = MagicMock()
    result.data = doc_data
    q = _make_query_mock()
    q.execute.return_value = result
    svc.table.return_value = q
    svc.storage.from_.return_value = _make_storage_mock(pdf_bytes)
    return svc


def _pdf_doc(file_type: str = "pdf", redacted_path: str | None = None) -> dict:
    return {
        "id": DOC_ID,
        "client_id": CLIENT_ID,
        "file_name": "financials.pdf",
        "file_path": f"{CLIENT_ID}/abc123.pdf",
        "file_type": file_type,
        "document_type": "profit_and_loss",
        "financial_year": 2024,
        "nature": "audited",
        "extraction_status": "pending",
        "source_unit": "rupees",
        "uploaded_by": "admin-uuid-0001",
        "uploaded_at": "2025-01-01T00:00:00+00:00",
        "original_page_count": None,
        "filtered_file_path": None,
        "removed_pages": None,
        "redacted_file_path": redacted_path,
        "redaction_terms": None,
        "redaction_count": None,
    }


# ── POST /{document_id}/detect-names ───────────────────────────────────────────


class TestDetectNames:
    def test_pdf_returns_detected_names(self, admin_client):
        """POST detect-names for a PDF with company name in header → 200 with names."""
        pdf_bytes = _create_test_pdf("ABC Industries Private Limited")
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(f"/api/documents/{DOC_ID}/detect-names")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == DOC_ID
        assert "detected_names" in data
        assert isinstance(data["detected_names"], list)

    def test_xlsx_returns_400(self, admin_client):
        """POST detect-names for an xlsx → 400."""
        svc = _mock_service(_pdf_doc(file_type="xlsx"))

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(f"/api/documents/{DOC_ID}/detect-names")

        assert response.status_code == 400

    def test_document_not_found_returns_404(self, admin_client):
        """POST detect-names for non-existent doc → 404."""
        svc = _mock_service(None)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(f"/api/documents/nonexistent/detect-names")

        assert response.status_code == 404


# ── POST /{document_id}/preview-redaction ──────────────────────────────────────


class TestPreviewRedaction:
    def test_returns_term_counts(self, admin_client):
        """POST preview-redaction with valid terms → 200 with counts."""
        pdf_bytes = _create_test_pdf("ABC Industries Private Limited")
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/preview-redaction",
                json={"terms": ["ABC Industries Private Limited"]},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == DOC_ID
        assert "term_counts" in data
        assert "total_instances" in data
        assert data["total_instances"] >= 1

    def test_empty_terms_returns_400(self, admin_client):
        """POST preview-redaction with empty terms → 400."""
        svc = _mock_service(_pdf_doc(), b"")

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/preview-redaction",
                json={"terms": []},
            )

        assert response.status_code == 400

    def test_xlsx_returns_400(self, admin_client):
        """POST preview-redaction for xlsx → 400."""
        svc = _mock_service(_pdf_doc(file_type="xlsx"))

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/preview-redaction",
                json={"terms": ["ABC"]},
            )

        assert response.status_code == 400


# ── POST /{document_id}/apply-redaction ────────────────────────────────────────


class TestApplyRedaction:
    def test_returns_redaction_response(self, admin_client):
        """POST apply-redaction with valid terms → 200 with redacted path."""
        pdf_bytes = _create_test_pdf("ABC Industries Private Limited")
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/apply-redaction",
                json={"terms": ["ABC Industries Private Limited"]},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == DOC_ID
        assert data["redacted_file_path"].endswith("_redacted.pdf")
        assert data["redaction_count"] >= 1
        assert "per_term_counts" in data

    def test_uploads_redacted_to_storage(self, admin_client):
        """POST apply-redaction uploads a file to storage."""
        pdf_bytes = _create_test_pdf("XYZ Pvt Ltd")
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            admin_client.post(
                f"/api/documents/{DOC_ID}/apply-redaction",
                json={"terms": ["XYZ Pvt Ltd"]},
            )

        svc.storage.from_.return_value.upload.assert_called_once()
        call_args = svc.storage.from_.return_value.upload.call_args
        uploaded_path = call_args[0][0]
        assert uploaded_path.endswith("_redacted.pdf")

    def test_updates_db_with_redacted_path(self, admin_client):
        """POST apply-redaction writes redacted_file_path and redaction_count to DB."""
        pdf_bytes = _create_test_pdf("ABC Industries Private Limited")
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            admin_client.post(
                f"/api/documents/{DOC_ID}/apply-redaction",
                json={"terms": ["ABC Industries Private Limited"]},
            )

        update_call = svc.table.return_value.update.call_args
        payload = update_call[0][0]
        assert "redacted_file_path" in payload
        assert "redaction_count" in payload
        assert "redaction_terms" in payload

    def test_empty_terms_returns_400(self, admin_client):
        """POST apply-redaction with empty terms → 400."""
        svc = _mock_service(_pdf_doc(), b"")

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/apply-redaction",
                json={"terms": []},
            )

        assert response.status_code == 400

    def test_xlsx_returns_400(self, admin_client):
        """POST apply-redaction for xlsx → 400."""
        svc = _mock_service(_pdf_doc(file_type="xlsx"))

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/apply-redaction",
                json={"terms": ["ABC"]},
            )

        assert response.status_code == 400
