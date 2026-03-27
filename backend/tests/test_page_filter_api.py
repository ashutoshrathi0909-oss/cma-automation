"""
Page filter API tests — GET /{id}/page-count and POST /{id}/filter-pages.

TDD: RED → GREEN → REFACTOR.
All tests mock Supabase and pikepdf; no real I/O.
"""

import io
from unittest.mock import MagicMock, patch

import pikepdf
import pytest

# ── Constants ──────────────────────────────────────────────────────────────────

DOC_ID = "doc-uuid-pdf-0001"
CLIENT_ID = "client-uuid-0001"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_minimal_pdf(page_count: int = 5) -> bytes:
    """Return a valid in-memory PDF with the given number of blank pages."""
    buf = io.BytesIO()
    with pikepdf.Pdf.new() as pdf:
        for _ in range(page_count):
            page = pikepdf.Page(
                pikepdf.Dictionary(
                    Type=pikepdf.Name("/Page"),
                    MediaBox=[0, 0, 612, 792],
                )
            )
            pdf.pages.append(page)
        pdf.save(buf)
    return buf.getvalue()


def _make_query_mock():
    """Self-chaining query builder mock."""
    q = MagicMock()
    for method in (
        "select", "insert", "update", "delete",
        "eq", "neq", "ilike", "order", "single", "limit",
    ):
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


def _pdf_doc(file_type: str = "pdf") -> dict:
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
    }


# ── GET /{document_id}/page-count ──────────────────────────────────────────────


class TestGetPageCount:
    def test_pdf_returns_200_with_count(self, admin_client):
        """GET page-count for a valid PDF → 200 with correct page count."""
        pdf_bytes = _make_minimal_pdf(page_count=8)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/documents/{DOC_ID}/page-count")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == DOC_ID
        assert data["page_count"] == 8

    def test_xlsx_returns_400(self, admin_client):
        """GET page-count for an xlsx document → 400 (not a PDF)."""
        svc = _mock_service(_pdf_doc(file_type="xlsx"))

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/documents/{DOC_ID}/page-count")

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_xls_returns_400(self, admin_client):
        """GET page-count for an xls document → 400 (not a PDF)."""
        svc = _mock_service(_pdf_doc(file_type="xls"))

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/documents/{DOC_ID}/page-count")

        assert response.status_code == 400

    def test_document_not_found_returns_404(self, admin_client):
        """GET page-count for a non-existent document → 404."""
        svc = _mock_service(None)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.get(f"/api/documents/nonexistent/page-count")

        assert response.status_code == 404

    def test_updates_original_page_count_in_db(self, admin_client):
        """GET page-count writes original_page_count to DB when not yet set."""
        pdf_bytes = _make_minimal_pdf(page_count=3)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            admin_client.get(f"/api/documents/{DOC_ID}/page-count")

        # The DB update should have been called
        svc.table.return_value.update.assert_called_once_with({"original_page_count": 3})

    @pytest.mark.skip(reason="DISABLE_AUTH=true in dev/CI container bypasses JWT; auth enforced in prod")
    def test_requires_auth(self, client):
        """GET page-count without auth → 401."""
        response = client.get(f"/api/documents/{DOC_ID}/page-count")
        assert response.status_code == 401


# ── POST /{document_id}/filter-pages ──────────────────────────────────────────


class TestFilterPages:
    def test_valid_range_returns_200(self, admin_client):
        """POST filter-pages with valid range → 200 with correct counts."""
        pdf_bytes = _make_minimal_pdf(page_count=10)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": "1-2, 7"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == DOC_ID
        assert data["original_page_count"] == 10
        assert data["removed_pages"] == [1, 2, 7]
        assert data["filtered_page_count"] == 7

    def test_single_page_removal(self, admin_client):
        """POST filter-pages removing exactly one page → 200."""
        pdf_bytes = _make_minimal_pdf(page_count=5)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": "3"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["removed_pages"] == [3]
        assert data["filtered_page_count"] == 4

    def test_empty_range_returns_400(self, admin_client):
        """POST filter-pages with an empty string → 400 (nothing to remove)."""
        pdf_bytes = _make_minimal_pdf(page_count=5)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch(
            "app.routers.documents.get_service_client", return_value=svc
        ), patch(
            "app.routers.documents.get_page_count", return_value=5
        ), patch(
            "app.routers.documents.parse_page_ranges", return_value=[]
        ):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": ""},
            )

        assert response.status_code == 400
        assert "No valid pages" in response.json()["detail"]

    def test_out_of_bounds_range_returns_400(self, admin_client):
        """POST filter-pages with only out-of-bounds pages → 400."""
        pdf_bytes = _make_minimal_pdf(page_count=5)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch(
            "app.routers.documents.get_service_client", return_value=svc
        ), patch(
            "app.routers.documents.get_page_count", return_value=5
        ), patch(
            "app.routers.documents.parse_page_ranges", return_value=[]
        ):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": "99-200"},
            )

        assert response.status_code == 400

    def test_non_pdf_returns_400(self, admin_client):
        """POST filter-pages for an xlsx document → 400."""
        svc = _mock_service(_pdf_doc(file_type="xlsx"))

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": "1"},
            )

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_document_not_found_returns_404(self, admin_client):
        """POST filter-pages for a non-existent document → 404."""
        svc = _mock_service(None)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            response = admin_client.post(
                f"/api/documents/nonexistent/filter-pages",
                json={"pages_to_remove": "1"},
            )

        assert response.status_code == 404

    def test_filtered_pdf_uploaded_to_storage(self, admin_client):
        """POST filter-pages uploads the filtered PDF to Storage."""
        pdf_bytes = _make_minimal_pdf(page_count=5)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": "1"},
            )

        svc.storage.from_.return_value.upload.assert_called_once()
        call_args = svc.storage.from_.return_value.upload.call_args
        uploaded_path = call_args[0][0]
        assert uploaded_path.endswith("_filtered.pdf")

    def test_db_updated_with_filtered_path(self, admin_client):
        """POST filter-pages writes filtered_file_path, removed_pages, original_page_count to DB."""
        pdf_bytes = _make_minimal_pdf(page_count=6)
        svc = _mock_service(_pdf_doc(), pdf_bytes)

        with patch("app.routers.documents.get_service_client", return_value=svc):
            admin_client.post(
                f"/api/documents/{DOC_ID}/filter-pages",
                json={"pages_to_remove": "1, 2"},
            )

        update_call = svc.table.return_value.update.call_args
        payload = update_call[0][0]
        assert "filtered_file_path" in payload
        assert payload["removed_pages"] == [1, 2]
        assert payload["original_page_count"] == 6

    @pytest.mark.skip(reason="DISABLE_AUTH=true in dev/CI container bypasses JWT; auth enforced in prod")
    def test_requires_auth(self, client):
        """POST filter-pages without auth → 401."""
        response = client.post(
            f"/api/documents/{DOC_ID}/filter-pages",
            json={"pages_to_remove": "1"},
        )
        assert response.status_code == 401
