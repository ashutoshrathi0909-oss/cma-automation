"""Tests for ExcelGenerator — Phase 7.

Split into two groups:
  1. Pure layer tests (use real openpyxl workbook, no DB/file I/O mocking)
     — test fill_workbook(), _fill_headers(), _fill_data_cells()
  2. Integration layer tests (mock DB, file I/O, storage)
     — test generate(), _save_upload_cleanup()
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import openpyxl
import pytest
from openpyxl.utils import column_index_from_string

from app.services.excel_generator import ExcelGenerator


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_ws() -> tuple[openpyxl.Workbook, object]:
    """Return a minimal workbook + its INPUT SHEET worksheet."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "INPUT SHEET"
    return wb, ws


def _make_generator() -> ExcelGenerator:
    """ExcelGenerator with mocked service (pure layer tests don't need DB)."""
    return ExcelGenerator(service=MagicMock(), template_path="/fake/template.xlsm")


# ── Pure layer tests ───────────────────────────────────────────────────────


def test_generator_fills_client_name_in_header():
    """Client name is written to row 7, column 1 (label column A)."""
    _, ws = _make_ws()
    gen = _make_generator()

    gen.fill_workbook(ws, client_name="Sharma & Sons Ltd", docs=[], cell_data=[])

    assert ws.cell(row=7, column=1).value == "Sharma & Sons Ltd"


def test_generator_fills_year_headers():
    """All 7 year columns (B-H) rewritten starting from base year."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2024, "nature": "audited"}]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=[])

    # base=2024 → B=2024, C=2025, D=2026, ..., H=2030
    assert ws.cell(row=8, column=2).value == 2024
    assert ws.cell(row=8, column=3).value == 2025
    assert ws.cell(row=8, column=8).value == 2030
    # Nature: 2024 is historical, rest are projected
    assert ws.cell(row=10, column=2).value == "audited"
    assert ws.cell(row=10, column=3).value == "Projected"


def test_generator_fills_nature_of_financials():
    """Historical docs get their nature; projection columns get 'Projected'."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [
        {"financial_year": 2024, "nature": "audited"},
        {"financial_year": 2025, "nature": "provisional"},
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=[])

    # base=2024 → B=2024(audited), C=2025(provisional), D+=Projected
    assert ws.cell(row=10, column=2).value == "audited"
    assert ws.cell(row=10, column=3).value == "provisional"
    assert ws.cell(row=10, column=4).value == "Projected"


def test_generator_fills_pnl_domestic_sales_row_22():
    """'Domestic Sales' (PNL row 22) is filled for financial year 2024."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2024, "nature": "audited"}]
    cell_data = [{"cma_field_name": "Domestic Sales", "financial_year": 2024, "amount": 500_000.0}]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Only year is 2024 → base=2024 → column B → index 2
    assert ws.cell(row=22, column=2).value == 500_000.0


def test_generator_fills_pnl_wages_row_45():
    """'Wages' (PNL row 45) is filled correctly."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2023, "nature": "audited"}]
    cell_data = [{"cma_field_name": "Wages", "financial_year": 2023, "amount": 120_000.0}]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Only year is 2023 → base=2023 → column B → index 2
    assert ws.cell(row=45, column=2).value == 120_000.0


def test_generator_fills_bs_share_capital_row_116():
    """'Issued, Subscribed and Paid up' (BS row 116) is filled correctly."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2024, "nature": "audited"}]
    cell_data = [
        {
            "cma_field_name": "Issued, Subscribed and Paid up",
            "financial_year": 2024,
            "amount": 1_000_000.0,
        }
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Only year is 2024 → base=2024 → column B → index 2
    assert ws.cell(row=116, column=2).value == 1_000_000.0


def test_generator_fills_bs_debtors_row_206():
    """'Domestic Receivables' (BS row 206) is filled correctly."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2025, "nature": "audited"}]
    cell_data = [
        {"cma_field_name": "Domestic Receivables", "financial_year": 2025, "amount": 250_000.0}
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Only year is 2025 → base=2025 → column B → index 2
    assert ws.cell(row=206, column=2).value == 250_000.0


def test_generator_maps_year_to_correct_column():
    """Each year maps to the correct Excel column dynamically."""
    _, ws = _make_ws()
    gen = _make_generator()

    # Docs with 4 years → base=2023 → 2023=B(2), 2024=C(3), 2025=D(4), 2026=E(5)
    years = [2023, 2024, 2025, 2026]
    docs = [{"financial_year": yr, "nature": "audited"} for yr in years]
    year_to_expected_col = {2023: 2, 2024: 3, 2025: 4, 2026: 5}
    cell_data = [
        {"cma_field_name": "Domestic Sales", "financial_year": yr, "amount": 1.0}
        for yr in years
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    for yr, col in year_to_expected_col.items():
        assert ws.cell(row=22, column=col).value == 1.0, f"Year {yr} → col {col} failed"


def test_generator_handles_multiple_years():
    """Data for different years lands in different columns."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [
        {"financial_year": 2024, "nature": "audited"},
        {"financial_year": 2025, "nature": "provisional"},
    ]
    cell_data = [
        {"cma_field_name": "Wages", "financial_year": 2024, "amount": 100.0},
        {"cma_field_name": "Wages", "financial_year": 2025, "amount": 200.0},
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # base=2024 → 2024=B(2), 2025=C(3)
    assert ws.cell(row=45, column=2).value == 100.0  # 2024 → col B
    assert ws.cell(row=45, column=3).value == 200.0  # 2025 → col C


def test_generator_sums_multiple_items_same_row():
    """Multiple line items mapping to the same (field_name, year) are summed."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2024, "nature": "audited"}]
    cell_data = [
        {"cma_field_name": "Domestic Sales", "financial_year": 2024, "amount": 300_000.0},
        {"cma_field_name": "Domestic Sales", "financial_year": 2024, "amount": 200_000.0},
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Only year is 2024 → base=2024 → column B → index 2
    assert ws.cell(row=22, column=2).value == 500_000.0


def test_generator_does_not_overwrite_formula_cells():
    """Cells not in PNL_FIELD_TO_ROW / BS_FIELD_TO_ROW are left untouched."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2023, "nature": "audited"}]

    # Row 21 is NOT in PNL_FIELD_TO_ROW (first mapping entry is row 22)
    ws.cell(row=21, column=2).value = "=SUM(B17:B20)"
    cell_data = [
        {"cma_field_name": "Domestic Sales", "financial_year": 2023, "amount": 999.0}
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Only year is 2023 → base=2023 → column B → index 2
    assert ws.cell(row=22, column=2).value == 999.0
    # Row 21 formula should be UNTOUCHED
    assert ws.cell(row=21, column=2).value == "=SUM(B17:B20)"


# ── Integration layer tests ────────────────────────────────────────────────
# These mock: openpyxl.load_workbook, service.storage, os.unlink, log_action


def _build_full_mock_service() -> MagicMock:
    """Builds a mock Supabase service with all needed chains pre-configured."""
    service = MagicMock()

    report_row = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "client_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "document_ids": ["doc-ccc"],
    }
    client_row = {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Test Client Ltd"}
    doc_row = {"id": "doc-ccc", "financial_year": 2024, "nature": "audited"}
    item_row = {"id": "item-ddd", "document_id": "doc-ccc", "amount": 100.0}
    clf_row = {"line_item_id": "item-ddd", "cma_field_name": "Domestic Sales"}

    def table_side_effect(name: str):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.in_.return_value = chain
        chain.single.return_value = chain
        chain.update.return_value = chain

        if name == "cma_reports":
            chain.execute.return_value = MagicMock(data=report_row)
        elif name == "clients":
            chain.execute.return_value = MagicMock(data=client_row)
        elif name == "documents":
            chain.execute.return_value = MagicMock(data=[doc_row])
        elif name == "extracted_line_items":
            chain.execute.return_value = MagicMock(data=[item_row])
        elif name == "classifications":
            chain.execute.return_value = MagicMock(data=[clf_row])
        else:
            chain.execute.return_value = MagicMock(data=[])
        return chain

    service.table.side_effect = table_side_effect

    storage_bucket = MagicMock()
    storage_bucket.upload.return_value = {"Key": "cma_reports/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/output.xlsm"}
    service.storage.from_.return_value = storage_bucket

    return service


def _make_mock_wb():
    """Minimal mock workbook + worksheet for integration tests."""
    ws = MagicMock()
    cell_mock = MagicMock()
    ws.cell.return_value = cell_mock
    wb = MagicMock()
    wb.__getitem__ = lambda s, k: ws
    return wb, ws


def test_generator_opens_template_with_keep_vba():
    """load_workbook is called with keep_vba=True."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        mock_load.return_value, _ = _make_mock_wb()
        gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
        gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    mock_load.assert_called_once_with("/fake/CMA.xlsm", keep_vba=True)


def test_generator_preserves_macros():
    """Same as above: keep_vba=True ensures VBA/macros are retained."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        mock_load.return_value, _ = _make_mock_wb()
        gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
        gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    _, kwargs = mock_load.call_args
    assert kwargs.get("keep_vba") is True


def test_generator_saves_as_xlsm():
    """Workbook is saved with a .xlsm extension (never .xlsx)."""
    service = _build_full_mock_service()
    saved_paths = []

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        wb_mock.save.side_effect = lambda p: saved_paths.append(p)
        mock_load.return_value = wb_mock

        gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
        gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    assert saved_paths, "wb.save was never called"
    assert saved_paths[0].endswith(".xlsm"), f"Expected .xlsm, got: {saved_paths[0]}"


def test_generator_uploads_to_supabase_storage():
    """Generated file is uploaded to the 'generated' Supabase Storage bucket."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
        storage_path = gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    service.storage.from_.assert_called_with("generated")
    service.storage.from_().upload.assert_called_once()
    assert storage_path == "cma_reports/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/output.xlsm"


def test_generator_logs_audit_trail():
    """log_action is called after successful upload."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        with patch("app.services.excel_generator.log_action") as mock_log:
            gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
            gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    mock_log.assert_called_once()
    args = mock_log.call_args[0]
    assert args[2] == "excel_generated"
    assert args[3] == "cma_report"
    assert args[4] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_generator_cleans_up_temp_file():
    """Temp .xlsm file is deleted after upload, even on success."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        with patch("app.services.excel_generator.os.unlink") as mock_unlink:
            gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
            gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    mock_unlink.assert_called_once()
    unlinked = mock_unlink.call_args[0][0]
    assert unlinked.endswith(".xlsm"), f"Expected .xlsm cleanup, got: {unlinked}"


# ── Branch coverage tests (edge cases for 100% coverage) ──────────────────


def test_fill_headers_writes_all_years_from_any_base():
    """Any base year maps correctly — B through H get sequential years."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 1900, "nature": "audited"}]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=[])

    # base=1900 → B=1900, C=1901, ..., H=1906
    assert ws.cell(row=8, column=2).value == 1900
    assert ws.cell(row=8, column=8).value == 1906
    assert ws.cell(row=10, column=2).value == "audited"
    assert ws.cell(row=10, column=3).value == "Projected"


def test_fill_data_cells_skips_unknown_field_and_year():
    """_fill_data_cells silently skips items with unknown field or year."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2024, "nature": "audited"}]
    cell_data = [
        {"cma_field_name": "Nonexistent Field XYZ", "financial_year": 2024, "amount": 999.0},
        {"cma_field_name": "Domestic Sales", "financial_year": 1900, "amount": 888.0},
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Unknown field: skipped. Year 1900 not in year_map (only 2024): skipped.
    # Row 22 col B (index 2) should be None because the only valid-year item had unknown field
    for col in range(1, 10):
        assert ws.cell(row=22, column=col).value is None


def test_fetch_report_raises_when_not_found():
    """_fetch_report raises ValueError when the report row is missing."""
    service = MagicMock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.single.return_value = chain
    chain.execute.return_value = MagicMock(data=None)
    service.table.return_value = chain

    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    with pytest.raises(ValueError, match="CMA report not found"):
        gen._fetch_report("missing-id")


def test_fetch_client_name_raises_when_not_found():
    """_fetch_client_name raises ValueError when the client row is missing."""
    service = MagicMock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.single.return_value = chain
    chain.execute.return_value = MagicMock(data=None)
    service.table.return_value = chain

    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    with pytest.raises(ValueError, match="Client not found"):
        gen._fetch_client_name("missing-client")


def test_fetch_documents_returns_empty_for_no_ids():
    """_fetch_documents returns [] immediately when given an empty list."""
    gen = ExcelGenerator(service=MagicMock(), template_path="/fake/CMA.xlsm")
    result = gen._fetch_documents([])
    assert result == []


def test_fetch_classified_data_returns_empty_for_no_ids():
    """_fetch_classified_data returns [] immediately when given an empty list."""
    gen = ExcelGenerator(service=MagicMock(), template_path="/fake/CMA.xlsm")
    result = gen._fetch_classified_data([], {})
    assert result == []


def test_fetch_classified_data_returns_empty_when_no_items():
    """_fetch_classified_data returns [] when no extracted_line_items exist."""
    service = MagicMock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.in_.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    service.table.return_value = chain

    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    result = gen._fetch_classified_data(["doc-1"], {"doc-1": 2024})
    assert result == []


def test_fetch_classified_data_skips_clf_without_field_name():
    """_fetch_classified_data skips classifications with no cma_field_name."""
    service = MagicMock()
    item_row = {"id": "item-1", "document_id": "doc-1", "amount": 50.0}
    clf_row_no_field = {"line_item_id": "item-1", "cma_field_name": None}

    def table_side_effect(name):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.in_.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = MagicMock(data=[])
        if name == "extracted_line_items":
            chain.execute.return_value = MagicMock(data=[item_row])
        elif name == "classifications":
            chain.execute.return_value = MagicMock(data=[clf_row_no_field])
        return chain

    service.table.side_effect = table_side_effect
    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    result = gen._fetch_classified_data(["doc-1"], {"doc-1": 2024})
    assert result == []


def test_fetch_classified_data_skips_clf_with_unknown_item():
    """_fetch_classified_data skips classifications whose line_item_id is not in items."""
    service = MagicMock()
    item_row = {"id": "item-1", "document_id": "doc-1", "amount": 50.0}
    clf_row_orphan = {"line_item_id": "item-UNKNOWN", "cma_field_name": "Wages"}

    def table_side_effect(name):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.in_.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = MagicMock(data=[])
        if name == "extracted_line_items":
            chain.execute.return_value = MagicMock(data=[item_row])
        elif name == "classifications":
            chain.execute.return_value = MagicMock(data=[clf_row_orphan])
        return chain

    service.table.side_effect = table_side_effect
    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    result = gen._fetch_classified_data(["doc-1"], {"doc-1": 2024})
    assert result == []


def test_fetch_classified_data_skips_item_without_year():
    """_fetch_classified_data skips items whose document has no year mapping."""
    service = MagicMock()
    item_row = {"id": "item-1", "document_id": "doc-ORPHAN", "amount": 50.0}
    clf_row = {"line_item_id": "item-1", "cma_field_name": "Wages"}
    # doc_years does not contain doc-ORPHAN → year lookup returns None → item skipped

    def table_side_effect(name):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.in_.return_value = chain
        chain.eq.return_value = chain
        chain.execute.return_value = MagicMock(data=[])
        if name == "extracted_line_items":
            chain.execute.return_value = MagicMock(data=[item_row])
        elif name == "classifications":
            chain.execute.return_value = MagicMock(data=[clf_row])
        return chain

    service.table.side_effect = table_side_effect
    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    # Pass a non-empty doc_years but with a different doc id — year lookup will miss
    result = gen._fetch_classified_data(["doc-ORPHAN"], {"doc-OTHER": 2024})
    assert result == []


def test_fetch_classified_data_filters_out_doubt_items():
    """_fetch_classified_data calls .eq('is_doubt', False) on classifications query — doubt items never silently classified."""
    service = MagicMock()

    # Items exist
    items_chain = MagicMock()
    items_chain.select.return_value = items_chain
    items_chain.in_.return_value = items_chain
    items_chain.execute.return_value = MagicMock(data=[{"id": "item-1", "document_id": "doc-1", "amount": 100.0}])

    # Classifications chain — capture the eq call
    clf_chain = MagicMock()
    clf_chain.select.return_value = clf_chain
    clf_chain.in_.return_value = clf_chain
    clf_chain.eq.return_value = clf_chain
    clf_chain.execute.return_value = MagicMock(data=[])

    def table_se(name):
        if name == "extracted_line_items":
            return items_chain
        elif name == "classifications":
            return clf_chain
        chain = MagicMock()
        chain.select.return_value = chain
        chain.in_.return_value = chain
        chain.execute.return_value = MagicMock(data=[])
        return chain

    service.table.side_effect = table_se

    gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
    doc_years = {"doc-1": 2024}
    gen._fetch_classified_data(["doc-1"], doc_years)

    # CRITICAL: verify is_doubt=False filter was applied
    clf_chain.eq.assert_called_once_with("is_doubt", False)


def test_generator_swallows_oserror_on_temp_cleanup():
    """OSError during temp file cleanup is swallowed (logged as warning, not raised)."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        with patch("app.services.excel_generator.os.unlink", side_effect=OSError("locked")):
            gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
            # Should NOT raise — OSError is caught and logged
            storage_path = gen.generate(report_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", user_id="user-xxx")

    assert storage_path == "cma_reports/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/output.xlsm"


def test_save_upload_cleanup_rejects_non_uuid_report_id():
    """_save_upload_cleanup raises ValueError for non-UUID report_id (path traversal guard)."""
    gen = ExcelGenerator(service=MagicMock(), template_path="/fake/CMA.xlsm")
    wb = openpyxl.Workbook()

    with pytest.raises(ValueError, match="Invalid report_id format"):
        gen._save_upload_cleanup(wb, "../../etc/passwd", "user-xxx")


def test_fill_data_cells_skips_formula_cells():
    """_fill_data_cells does not overwrite cells that already contain a real formula."""
    _, ws = _make_ws()
    # Pre-set a formula in the Domestic Sales cell (row 22, col B = col 2, for year 2023)
    ws.cell(row=22, column=2).value = "=SUM(C22:D22)"
    gen = _make_generator()
    docs = [{"financial_year": 2023, "nature": "audited"}]

    cell_data = [{"cma_field_name": "Domestic Sales", "financial_year": 2023, "amount": 99999.0}]
    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=cell_data)

    # Real formula must be preserved — not overwritten with the data amount
    assert ws.cell(row=22, column=2).value == "=SUM(C22:D22)"
