"""Tests for roll_forward_service — compute, preview, confirm."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.roll_forward_service import (
    compute_roll_forward,
    preview_roll_forward,
    confirm_roll_forward,
)


# ── compute_roll_forward tests ────────────────────────────────────────────


class TestComputeRollForward:
    """Pure function tests — no mocking needed."""

    def test_full_3_years(self):
        result = compute_roll_forward([2021, 2022, 2023])
        assert result["drop_year"] == 2021
        assert result["keep_years"] == [2022, 2023]
        assert result["add_year"] == 2024
        assert result["target_years"] == [2022, 2023, 2024]

    def test_only_2_years(self):
        result = compute_roll_forward([2022, 2023])
        assert result["drop_year"] is None
        assert result["keep_years"] == [2022, 2023]
        assert result["add_year"] == 2024
        assert result["target_years"] == [2022, 2023, 2024]

    def test_only_1_year(self):
        result = compute_roll_forward([2023])
        assert result["drop_year"] is None
        assert result["keep_years"] == [2023]
        assert result["add_year"] == 2024
        assert result["target_years"] == [2023, 2024]

    def test_non_contiguous_years(self):
        result = compute_roll_forward([2020, 2022, 2023])
        assert result["drop_year"] == 2020
        assert result["keep_years"] == [2022, 2023]
        assert result["add_year"] == 2024

    def test_unsorted_input(self):
        result = compute_roll_forward([2023, 2021, 2022])
        assert result["drop_year"] == 2021
        assert result["keep_years"] == [2022, 2023]
        assert result["add_year"] == 2024
        assert result["target_years"] == [2022, 2023, 2024]

    def test_max_historical_4(self):
        result = compute_roll_forward([2020, 2021, 2022, 2023], max_historical=4)
        assert result["drop_year"] == 2020
        assert result["keep_years"] == [2021, 2022, 2023]
        assert result["add_year"] == 2024

    def test_fewer_than_max_historical(self):
        result = compute_roll_forward([2022, 2023], max_historical=4)
        assert result["drop_year"] is None
        assert result["keep_years"] == [2022, 2023]
        assert result["add_year"] == 2024


# ── Mock helpers ──────────────────────────────────────────────────────────


def _mock_service(table_responses: dict | None = None):
    """Build a mock Supabase service client.

    table_responses maps table_name to a dict with method chains.
    """
    service = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if table_responses and name in table_responses:
            return table_responses[name]
        return mock_table

    service.table.side_effect = table_side_effect
    return service


def _chain_mock(data=None, count=None):
    """Create a chainable mock that returns data on .execute()."""
    mock = MagicMock()
    result = MagicMock()
    result.data = data
    result.count = count

    # Make all chainable methods return the same mock
    for method in ["select", "eq", "in_", "single", "order"]:
        getattr(mock, method).return_value = mock

    mock.execute.return_value = result
    return mock


# ── preview_roll_forward tests ────────────────────────────────────────────


class TestPreviewRollForward:
    @pytest.mark.asyncio
    async def test_rejects_non_complete_report(self):
        report_mock = _chain_mock(data={
            "id": "r1", "status": "draft", "client_id": "c1",
            "financial_years": [2021, 2022, 2023], "document_ids": [],
        })
        service = MagicMock()
        service.table.return_value = report_mock

        with pytest.raises(HTTPException) as exc_info:
            await preview_roll_forward(service, "r1", "c1")
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_wrong_client(self):
        report_mock = _chain_mock(data={
            "id": "r1", "status": "complete", "client_id": "c2",
            "financial_years": [2021, 2022, 2023], "document_ids": [],
        })
        service = MagicMock()
        service.table.return_value = report_mock

        with pytest.raises(HTTPException) as exc_info:
            await preview_roll_forward(service, "r1", "c1")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_report(self):
        report_mock = _chain_mock(data=None)
        service = MagicMock()
        service.table.return_value = report_mock

        with pytest.raises(HTTPException) as exc_info:
            await preview_roll_forward(service, "r1", "c1")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_blocking_when_no_new_docs(self):
        """Preview should show blocking_reasons when no FY24 docs exist."""
        call_count = [0]

        def table_side_effect(name):
            mock = MagicMock()
            for method in ["select", "eq", "in_", "single", "order"]:
                getattr(mock, method).return_value = mock

            if name == "cma_reports":
                result = MagicMock()
                result.data = {
                    "id": "r1", "status": "complete", "client_id": "c1",
                    "financial_years": [2021, 2022, 2023],
                    "document_ids": ["d1", "d2"],
                    "title": "Test Report",
                }
                mock.execute.return_value = result
            elif name == "documents":
                call_count[0] += 1
                result = MagicMock()
                if call_count[0] == 1:
                    # Source documents
                    result.data = [
                        {"id": "d1", "file_name": "bs2022.pdf", "financial_year": 2022,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "verified"},
                        {"id": "d2", "file_name": "bs2023.pdf", "financial_year": 2023,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "verified"},
                    ]
                else:
                    # New year docs query — empty
                    result.data = []
                mock.execute.return_value = result
            elif name == "extracted_line_items":
                result = MagicMock()
                result.data = [{"id": "li1"}, {"id": "li2"}]
                mock.execute.return_value = result
            elif name == "classifications":
                result = MagicMock()
                result.data = []
                result.count = 5
                mock.execute.return_value = result
            return mock

        service = MagicMock()
        service.table.side_effect = table_side_effect

        preview = await preview_roll_forward(service, "r1", "c1")
        assert preview["can_confirm"] is False
        assert len(preview["blocking_reasons"]) > 0
        assert "FY2024" in preview["blocking_reasons"][0]

    @pytest.mark.asyncio
    async def test_can_confirm_when_docs_ready(self):
        """Preview should return can_confirm=True when new docs are verified."""
        call_count = [0]

        def table_side_effect(name):
            mock = MagicMock()
            for method in ["select", "eq", "in_", "single", "order"]:
                getattr(mock, method).return_value = mock

            if name == "cma_reports":
                result = MagicMock()
                result.data = {
                    "id": "r1", "status": "complete", "client_id": "c1",
                    "financial_years": [2021, 2022, 2023],
                    "document_ids": ["d1", "d2"],
                    "title": "Test Report",
                }
                mock.execute.return_value = result
            elif name == "documents":
                call_count[0] += 1
                result = MagicMock()
                if call_count[0] == 1:
                    result.data = [
                        {"id": "d1", "file_name": "bs2022.pdf", "financial_year": 2022,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "verified"},
                        {"id": "d2", "file_name": "bs2023.pdf", "financial_year": 2023,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "verified"},
                    ]
                else:
                    result.data = [
                        {"id": "d3", "file_name": "bs2024.pdf", "financial_year": 2024,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "verified"},
                    ]
                mock.execute.return_value = result
            elif name == "extracted_line_items":
                result = MagicMock()
                result.data = [{"id": "li1"}]
                mock.execute.return_value = result
            elif name == "classifications":
                result = MagicMock()
                result.data = []
                result.count = 3
                mock.execute.return_value = result
            return mock

        service = MagicMock()
        service.table.side_effect = table_side_effect

        preview = await preview_roll_forward(service, "r1", "c1")
        assert preview["can_confirm"] is True
        assert preview["blocking_reasons"] == []
        assert preview["drop_year"] == 2021
        assert preview["keep_years"] == [2022, 2023]
        assert preview["add_year"] == 2024

    @pytest.mark.asyncio
    async def test_blocking_when_docs_unverified(self):
        """Preview should block when new docs exist but aren't verified."""
        call_count = [0]

        def table_side_effect(name):
            mock = MagicMock()
            for method in ["select", "eq", "in_", "single", "order"]:
                getattr(mock, method).return_value = mock

            if name == "cma_reports":
                result = MagicMock()
                result.data = {
                    "id": "r1", "status": "complete", "client_id": "c1",
                    "financial_years": [2021, 2022, 2023],
                    "document_ids": ["d1", "d2"],
                    "title": "Test Report",
                }
                mock.execute.return_value = result
            elif name == "documents":
                call_count[0] += 1
                result = MagicMock()
                if call_count[0] == 1:
                    result.data = [
                        {"id": "d1", "file_name": "bs2022.pdf", "financial_year": 2022,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "verified"},
                    ]
                else:
                    result.data = [
                        {"id": "d3", "file_name": "bs2024.pdf", "financial_year": 2024,
                         "nature": "audited", "document_type": "balance_sheet",
                         "extraction_status": "extracted"},
                    ]
                mock.execute.return_value = result
            elif name == "extracted_line_items":
                result = MagicMock()
                result.data = []
                mock.execute.return_value = result
            return mock

        service = MagicMock()
        service.table.side_effect = table_side_effect

        preview = await preview_roll_forward(service, "r1", "c1")
        assert preview["can_confirm"] is False
        assert any("not yet verified" in r for r in preview["blocking_reasons"])


# ── confirm_roll_forward tests ────────────────────────────────────────────


class TestConfirmRollForward:
    @pytest.mark.asyncio
    async def test_rejects_unverified_new_docs(self):
        call_count = [0]

        def table_side_effect(name):
            mock = MagicMock()
            for method in ["select", "eq", "in_", "single", "order"]:
                getattr(mock, method).return_value = mock

            if name == "cma_reports":
                result = MagicMock()
                result.data = {
                    "id": "r1", "status": "complete", "client_id": "c1",
                    "financial_years": [2021, 2022, 2023],
                    "document_ids": ["d1"],
                }
                mock.execute.return_value = result
            elif name == "documents":
                result = MagicMock()
                result.data = [
                    {"id": "d3", "file_name": "bs2024.pdf", "financial_year": 2024,
                     "client_id": "c1", "extraction_status": "extracted"},
                ]
                mock.execute.return_value = result
            return mock

        service = MagicMock()
        service.table.side_effect = table_side_effect

        with pytest.raises(HTTPException) as exc_info:
            await confirm_roll_forward(
                service, "r1", "c1", 2024, ["d3"], None, "lakhs", "u1"
            )
        assert exc_info.value.status_code == 400
        assert "not verified" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_rejects_wrong_year_docs(self):
        def table_side_effect(name):
            mock = MagicMock()
            for method in ["select", "eq", "in_", "single", "order"]:
                getattr(mock, method).return_value = mock

            if name == "cma_reports":
                result = MagicMock()
                result.data = {
                    "id": "r1", "status": "complete", "client_id": "c1",
                    "financial_years": [2021, 2022, 2023],
                    "document_ids": ["d1"],
                }
                mock.execute.return_value = result
            elif name == "documents":
                result = MagicMock()
                result.data = [
                    {"id": "d3", "file_name": "bs2023.pdf", "financial_year": 2023,
                     "client_id": "c1", "extraction_status": "verified"},
                ]
                mock.execute.return_value = result
            return mock

        service = MagicMock()
        service.table.side_effect = table_side_effect

        with pytest.raises(HTTPException) as exc_info:
            await confirm_roll_forward(
                service, "r1", "c1", 2024, ["d3"], None, "lakhs", "u1"
            )
        assert exc_info.value.status_code == 400
        assert "FY2023" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_creates_report_with_correct_data(self):
        """Successful confirm should create report with carried + new doc IDs."""
        call_count = {"documents": 0}
        inserted_report = None
        inserted_audit = None

        def table_side_effect(name):
            nonlocal inserted_report, inserted_audit
            mock = MagicMock()
            for method in ["select", "eq", "in_", "single", "order"]:
                getattr(mock, method).return_value = mock

            if name == "cma_reports":
                # First call is select, second is insert
                select_result = MagicMock()
                select_result.data = {
                    "id": "r1", "status": "complete", "client_id": "c1",
                    "financial_years": [2021, 2022, 2023],
                    "document_ids": ["d1", "d2", "d3"],
                }
                mock.execute.return_value = select_result

                def capture_insert(data):
                    nonlocal inserted_report
                    inserted_report = data
                    insert_mock = MagicMock()
                    insert_result = MagicMock()
                    insert_result.data = [{"id": "new-r1", **data}]
                    insert_mock.execute.return_value = insert_result
                    return insert_mock

                mock.insert.side_effect = capture_insert
            elif name == "documents":
                call_count["documents"] += 1
                result = MagicMock()
                if call_count["documents"] == 1:
                    # New docs validation
                    result.data = [
                        {"id": "d4", "file_name": "bs2024.pdf", "financial_year": 2024,
                         "client_id": "c1", "extraction_status": "verified",
                         "nature": "provisional"},
                    ]
                elif call_count["documents"] == 2:
                    # Carried docs
                    result.data = [
                        {"id": "d1", "financial_year": 2021},
                        {"id": "d2", "financial_year": 2022},
                        {"id": "d3", "financial_year": 2023},
                    ]
                elif call_count["documents"] == 3:
                    # year_natures
                    result.data = [
                        {"nature": "audited"},
                        {"nature": "audited"},
                        {"nature": "provisional"},
                    ]
                mock.execute.return_value = result
            elif name == "clients":
                result = MagicMock()
                result.data = {"name": "Test Corp"}
                mock.execute.return_value = result
            elif name == "cma_report_history":
                def capture_audit(data):
                    nonlocal inserted_audit
                    inserted_audit = data
                    audit_mock = MagicMock()
                    audit_result = MagicMock()
                    audit_result.data = [data]
                    audit_mock.execute.return_value = audit_result
                    return audit_mock
                mock.insert.side_effect = capture_audit
            return mock

        service = MagicMock()
        service.table.side_effect = table_side_effect

        result = await confirm_roll_forward(
            service, "r1", "c1", 2024, ["d4"], None, "lakhs", "u1"
        )

        assert result["new_report_id"] == "new-r1"
        assert result["status"] == "draft"
        assert "d4" in result["document_ids"]
        assert inserted_report is not None
        assert inserted_report["rolled_from_report_id"] == "r1"
        assert inserted_report["roll_forward_metadata"]["added_year"] == 2024
        assert inserted_audit is not None
        assert inserted_audit["action"] == "roll_forward_created"

    @pytest.mark.asyncio
    async def test_rejects_non_complete_report(self):
        report_mock = _chain_mock(data={
            "id": "r1", "status": "generating", "client_id": "c1",
            "financial_years": [2021, 2022, 2023], "document_ids": [],
        })
        service = MagicMock()
        service.table.return_value = report_mock

        with pytest.raises(HTTPException) as exc_info:
            await confirm_roll_forward(
                service, "r1", "c1", 2024, ["d3"], None, "lakhs", "u1"
            )
        assert exc_info.value.status_code == 400
