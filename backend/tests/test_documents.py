"""
Phase 3: Document upload & storage tests.

RED → GREEN → REFACTOR:
  RED:   Failing tests written before the router exists.
  GREEN: app/routers/documents.py makes them pass.
  REFACTOR: Clean up without breaking green.
"""

from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_DOCUMENT = {
    "id": "doc-uuid-0001",
    "client_id": "client-uuid-0001",
    "file_name": "financials_2024.pdf",
    "file_path": "client-uuid-0001/abc123.pdf",
    "file_type": "pdf",
    "document_type": "profit_and_loss",
    "financial_year": 2024,
    "nature": "audited",
    "extraction_status": "pending",
    "uploaded_by": "admin-uuid-0001",
    "uploaded_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_DOCUMENT_2 = {
    "id": "doc-uuid-0002",
    "client_id": "client-uuid-0001",
    "file_name": "balance_sheet_2024.xlsx",
    "file_path": "client-uuid-0001/def456.xlsx",
    "file_type": "xlsx",
    "document_type": "balance_sheet",
    "financial_year": 2024,
    "nature": "provisional",
    "extraction_status": "pending",
    "uploaded_by": "admin-uuid-0001",
    "uploaded_at": "2025-01-02T00:00:00+00:00",
}


def _mock_service(data):
    """
    Supabase service mock with both table and storage operations.
    Self-chaining query builder so any chain depth reaches .execute().
    """
    svc = MagicMock()
    result = MagicMock()
    result.data = data

    q = MagicMock()
    q.execute.return_value = result
    for method in (
        "select", "insert", "update", "delete",
        "eq", "neq", "ilike", "order", "single", "limit",
    ):
        getattr(q, method).return_value = q

    svc.table.return_value = q

    # Storage mock
    bucket = MagicMock()
    bucket.upload.return_value = MagicMock()
    bucket.remove.return_value = MagicMock()
    svc.storage.from_.return_value = bucket

    return svc


# ── Upload ─────────────────────────────────────────────────────────────────────


class TestUploadDocument:
    def test_upload_pdf_success(self, admin_client):
        """Upload a valid PDF → 201 with document record."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service([SAMPLE_DOCUMENT]),
        ):
            response = admin_client.post(
                "/api/documents/",
                files={"file": ("financials_2024.pdf", b"%PDF-1.4 content", "application/pdf")},
                data={
                    "client_id": "client-uuid-0001",
                    "document_type": "profit_and_loss",
                    "financial_year": "2024",
                    "nature": "audited",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["file_type"] == "pdf"
        assert data["client_id"] == "client-uuid-0001"

    def test_upload_xlsx_success(self, admin_client):
        """Upload a valid .xlsx file → 201."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service([SAMPLE_DOCUMENT_2]),
        ):
            response = admin_client.post(
                "/api/documents/",
                files={
                    "file": (
                        "balance_sheet.xlsx",
                        b"PK content",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={
                    "client_id": "client-uuid-0001",
                    "document_type": "balance_sheet",
                    "financial_year": "2024",
                    "nature": "provisional",
                },
            )

        assert response.status_code == 201
        assert response.json()["file_type"] == "xlsx"

    def test_upload_xls_success(self, admin_client):
        """Upload a valid .xls file → 201."""
        xls_doc = {**SAMPLE_DOCUMENT, "file_type": "xls", "file_name": "old_format.xls"}
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service([xls_doc]),
        ):
            response = admin_client.post(
                "/api/documents/",
                files={
                    "file": (
                        "old_format.xls",
                        b"D0CF11E0 content",
                        "application/vnd.ms-excel",
                    )
                },
                data={
                    "client_id": "client-uuid-0001",
                    "document_type": "profit_and_loss",
                    "financial_year": "2023",
                    "nature": "audited",
                },
            )

        assert response.status_code == 201
        assert response.json()["file_type"] == "xls"

    def test_upload_invalid_filetype_400(self, admin_client):
        """Upload a .txt file → 400 invalid file type."""
        response = admin_client.post(
            "/api/documents/",
            files={"file": ("notes.txt", b"plain text", "text/plain")},
            data={
                "client_id": "client-uuid-0001",
                "document_type": "profit_and_loss",
                "financial_year": "2024",
                "nature": "audited",
            },
        )
        assert response.status_code == 400

    def test_upload_sets_status_pending(self, admin_client):
        """Newly uploaded document always has extraction_status = 'pending'."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service([SAMPLE_DOCUMENT]),
        ):
            response = admin_client.post(
                "/api/documents/",
                files={"file": ("test.pdf", b"%PDF content", "application/pdf")},
                data={
                    "client_id": "client-uuid-0001",
                    "document_type": "profit_and_loss",
                    "financial_year": "2024",
                    "nature": "audited",
                },
            )

        assert response.status_code == 201
        assert response.json()["extraction_status"] == "pending"

    def test_upload_stores_in_supabase_storage(self, admin_client):
        """File bytes are sent to Supabase Storage on upload."""
        mock_svc = _mock_service([SAMPLE_DOCUMENT])
        with patch("app.routers.documents.get_service_client", return_value=mock_svc):
            admin_client.post(
                "/api/documents/",
                files={"file": ("test.pdf", b"%PDF content", "application/pdf")},
                data={
                    "client_id": "client-uuid-0001",
                    "document_type": "profit_and_loss",
                    "financial_year": "2024",
                    "nature": "audited",
                },
            )

        mock_svc.storage.from_.return_value.upload.assert_called_once()

    def test_upload_requires_document_type(self, admin_client):
        """Missing document_type form field → 422."""
        response = admin_client.post(
            "/api/documents/",
            files={"file": ("test.pdf", b"%PDF content", "application/pdf")},
            data={
                "client_id": "client-uuid-0001",
                # document_type intentionally omitted
                "financial_year": "2024",
                "nature": "audited",
            },
        )
        assert response.status_code == 422

    def test_upload_requires_financial_year(self, admin_client):
        """Missing financial_year form field → 422."""
        response = admin_client.post(
            "/api/documents/",
            files={"file": ("test.pdf", b"%PDF content", "application/pdf")},
            data={
                "client_id": "client-uuid-0001",
                "document_type": "profit_and_loss",
                # financial_year intentionally omitted
                "nature": "audited",
            },
        )
        assert response.status_code == 422


# ── List ───────────────────────────────────────────────────────────────────────


class TestListDocuments:
    def test_list_documents_for_client(self, admin_client):
        """List docs for a client → 200 with all documents."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service([SAMPLE_DOCUMENT, SAMPLE_DOCUMENT_2]),
        ):
            response = admin_client.get(
                "/api/documents/?client_id=client-uuid-0001"
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["client_id"] == "client-uuid-0001"

    def test_list_documents_empty(self, admin_client):
        """Client with no documents → 200 empty list."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service([]),
        ):
            response = admin_client.get(
                "/api/documents/?client_id=client-uuid-0001"
            )

        assert response.status_code == 200
        assert response.json() == []


# ── Delete ─────────────────────────────────────────────────────────────────────


class TestDeleteDocument:
    def test_delete_document_removes_file(self, admin_client):
        """DELETE calls Supabase Storage remove for the file."""
        mock_svc = _mock_service(SAMPLE_DOCUMENT)
        with patch("app.routers.documents.get_service_client", return_value=mock_svc):
            response = admin_client.delete("/api/documents/doc-uuid-0001")

        assert response.status_code == 204
        mock_svc.storage.from_.return_value.remove.assert_called_once()

    def test_delete_document_removes_db_record(self, admin_client):
        """DELETE removes the database record → 204."""
        mock_svc = _mock_service(SAMPLE_DOCUMENT)
        with patch("app.routers.documents.get_service_client", return_value=mock_svc):
            response = admin_client.delete("/api/documents/doc-uuid-0001")

        assert response.status_code == 204
        mock_svc.table.return_value.delete.assert_called_once()
