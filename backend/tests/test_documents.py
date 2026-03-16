"""
Phase 3: Document upload & storage tests.

RED → GREEN → REFACTOR:
  RED:   Failing tests written before the router exists.
  GREEN: app/routers/documents.py makes them pass.
  REFACTOR: Clean up without breaking green.
"""

from unittest.mock import MagicMock, patch

import pytest


# ── Sample data ────────────────────────────────────────────────────────────────

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

SAMPLE_CLIENT = {"id": "client-uuid-0001"}


# ── Mock helpers ───────────────────────────────────────────────────────────────


def _make_query_mock():
    """Self-chaining query builder mock — any chain depth reaches .execute()."""
    q = MagicMock()
    for method in (
        "select", "insert", "update", "delete",
        "eq", "neq", "ilike", "order", "single", "limit",
    ):
        getattr(q, method).return_value = q
    return q


def _make_storage_mock():
    bucket = MagicMock()
    bucket.upload.return_value = MagicMock()
    bucket.remove.return_value = MagicMock()
    return bucket


def _mock_service(data):
    """
    Single-result mock: every execute() call returns the same data.
    Use for simple single-query endpoints (e.g. delete).
    """
    svc = MagicMock()
    result = MagicMock()
    result.data = data

    q = _make_query_mock()
    q.execute.return_value = result
    svc.table.return_value = q
    svc.storage.from_.return_value = _make_storage_mock()
    return svc


def _mock_service_seq(*data_list):
    """
    Sequential mock: the N-th execute() call returns data_list[N-1].

    Upload endpoints make two round-trips:
      1. client existence check → should return SAMPLE_CLIENT / None
      2. document insert / list query → should return [doc] / []

    Example:
        _mock_service_seq(SAMPLE_CLIENT, [SAMPLE_DOCUMENT])
    """
    svc = MagicMock()

    results = [MagicMock(data=d) for d in data_list]
    q = _make_query_mock()
    q.execute.side_effect = results
    svc.table.return_value = q
    svc.storage.from_.return_value = _make_storage_mock()
    return svc


# ── Upload ─────────────────────────────────────────────────────────────────────


class TestUploadDocument:
    def test_upload_pdf_success(self, admin_client):
        """Upload a valid PDF → 201 with document record."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service_seq(SAMPLE_CLIENT, [SAMPLE_DOCUMENT]),
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
            return_value=_mock_service_seq(SAMPLE_CLIENT, [SAMPLE_DOCUMENT_2]),
        ):
            response = admin_client.post(
                "/api/documents/",
                files={
                    "file": (
                        "balance_sheet.xlsx",
                        b"PK\x03\x04 xlsx content",   # correct OOXML magic bytes
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
            return_value=_mock_service_seq(SAMPLE_CLIENT, [xls_doc]),
        ):
            response = admin_client.post(
                "/api/documents/",
                files={
                    "file": (
                        "old_format.xls",
                        b"\xd0\xcf\x11\xe0 xls content",  # correct OLE2 magic bytes
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
        """Upload a .txt file → 400 invalid file type (no DB call needed)."""
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

    def test_upload_magic_bytes_mismatch_400(self, admin_client):
        """File renamed to .pdf but contains non-PDF bytes → 400 (no DB call)."""
        response = admin_client.post(
            "/api/documents/",
            files={"file": ("malicious.pdf", b"MZ\x90\x00 this is an exe", "application/pdf")},
            data={
                "client_id": "client-uuid-0001",
                "document_type": "profit_and_loss",
                "financial_year": "2024",
                "nature": "audited",
            },
        )
        assert response.status_code == 400
        assert "content does not match" in response.json()["detail"]

    def test_upload_file_too_large_413(self, admin_client):
        """File exceeding 50 MB → 413 (rejected before storage call)."""
        # 50 MB + 1 byte — starts with valid PDF magic bytes so extension check passes
        large_content = b"%PDF" + b"x" * (50 * 1024 * 1024 - 3)
        response = admin_client.post(
            "/api/documents/",
            files={"file": ("huge.pdf", large_content, "application/pdf")},
            data={
                "client_id": "client-uuid-0001",
                "document_type": "profit_and_loss",
                "financial_year": "2024",
                "nature": "audited",
            },
        )
        assert response.status_code == 413
        assert "50 MB" in response.json()["detail"]

    def test_upload_nonexistent_client_404(self, admin_client):
        """Upload to a client_id that doesn't exist → 404."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service_seq(None),  # client check returns no data
        ):
            response = admin_client.post(
                "/api/documents/",
                files={"file": ("test.pdf", b"%PDF content", "application/pdf")},
                data={
                    "client_id": "nonexistent-client",
                    "document_type": "profit_and_loss",
                    "financial_year": "2024",
                    "nature": "audited",
                },
            )
        assert response.status_code == 404

    def test_upload_sets_status_pending(self, admin_client):
        """Newly uploaded document always has extraction_status = 'pending'."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service_seq(SAMPLE_CLIENT, [SAMPLE_DOCUMENT]),
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
        mock_svc = _mock_service_seq(SAMPLE_CLIENT, [SAMPLE_DOCUMENT])
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

    def test_storage_cleaned_up_on_db_failure(self, admin_client):
        """If the DB insert fails after storage upload, the orphaned file is removed."""
        # Client check returns valid client; DB insert returns empty → triggers cleanup
        mock_svc = _mock_service_seq(SAMPLE_CLIENT, [])
        with patch("app.routers.documents.get_service_client", return_value=mock_svc):
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

        assert response.status_code == 500
        mock_svc.storage.from_.return_value.remove.assert_called_once()

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
            return_value=_mock_service_seq(SAMPLE_CLIENT, [SAMPLE_DOCUMENT, SAMPLE_DOCUMENT_2]),
        ):
            response = admin_client.get("/api/documents/?client_id=client-uuid-0001")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["client_id"] == "client-uuid-0001"

    def test_list_documents_empty(self, admin_client):
        """Client with no documents → 200 empty list."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service_seq(SAMPLE_CLIENT, []),
        ):
            response = admin_client.get("/api/documents/?client_id=client-uuid-0001")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_documents_nonexistent_client_404(self, admin_client):
        """List docs for a client that doesn't exist → 404."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service_seq(None),
        ):
            response = admin_client.get("/api/documents/?client_id=nonexistent-client")

        assert response.status_code == 404


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

    def test_delete_nonexistent_document_404(self, admin_client):
        """DELETE a document that doesn't exist → 404."""
        with patch(
            "app.routers.documents.get_service_client",
            return_value=_mock_service(None),
        ):
            response = admin_client.delete("/api/documents/nonexistent-doc")

        assert response.status_code == 404


# ── Unauthenticated ────────────────────────────────────────────────────────────


class TestUnauthenticated:
    def test_upload_requires_auth(self, client):
        """Upload without auth token → 401."""
        response = client.post(
            "/api/documents/",
            files={"file": ("test.pdf", b"%PDF content", "application/pdf")},
            data={
                "client_id": "client-uuid-0001",
                "document_type": "profit_and_loss",
                "financial_year": "2024",
                "nature": "audited",
            },
        )
        assert response.status_code == 401

    def test_list_requires_auth(self, client):
        """List documents without auth token → 401."""
        response = client.get("/api/documents/?client_id=client-uuid-0001")
        assert response.status_code == 401

    def test_delete_requires_auth(self, client):
        """Delete document without auth token → 401."""
        response = client.delete("/api/documents/doc-uuid-0001")
        assert response.status_code == 401
