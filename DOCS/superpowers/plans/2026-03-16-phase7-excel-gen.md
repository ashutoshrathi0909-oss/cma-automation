# Phase 7 — Excel Generation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a macro-enabled CMA Excel file from reviewed classifications, enable download via a signed Supabase Storage URL, and surface a Generate/Download UI on the CMA report page.

**Architecture:** `ExcelGenerator` service has two layers — a pure `fill_workbook()` method (fully unit-testable without DB/file I/O) and a `generate()` method that orchestrates DB fetching, openpyxl file writing, Supabase Storage upload, audit logging, and temp-file cleanup. An ARQ background task (`run_excel_generation`) calls the generator and manages report status transitions. Two new API endpoints (`/generate` and `/download`) integrate with the existing `cma_reports` router.

**Tech Stack:** Python openpyxl (already in requirements.txt), arq (ARQ), Supabase Storage (bucket: `generated`), Next.js 15 App Router + shadcn/ui

---

## File Map

### New files
| File | Responsibility |
|------|---------------|
| `backend/app/services/excel_generator.py` | `ExcelGenerator` class — fills template, uploads to storage, audits, cleans up |
| `backend/app/workers/excel_tasks.py` | ARQ task `run_excel_generation(ctx, report_id)` — calls generator, updates report status |
| `backend/tests/test_excel_generator.py` | 100% coverage tests for `ExcelGenerator` |
| `backend/tests/test_excel_tasks.py` | Tests for `run_excel_generation` ARQ task |
| `DOCS/Setup/phase7_migration.sql` | SQL: add `output_path TEXT` column to `cma_reports` |
| `frontend/src/app/(app)/cma/[id]/generate/page.tsx` | Progress tracker + download button |

### Modified files
| File | Change |
|------|--------|
| `backend/app/models/schemas.py` | Add `GenerateTriggerResponse`, `DownloadUrlResponse`; add `output_path` to `CMAReportResponse` |
| `backend/app/routers/cma_reports.py` | Add POST `/generate` + GET `/download` endpoints |
| `backend/app/workers/worker.py` | Register `run_excel_generation` in `WorkerSettings.functions` |
| `backend/tests/test_cma_reports.py` | Add tests for `/generate` and `/download` endpoints |
| `frontend/src/app/(app)/cma/[id]/page.tsx` | Enable "Generate Excel" button (link to generate page when no doubts) |
| `frontend/src/types/index.ts` | Add `GenerateTriggerResponse`, `DownloadUrlResponse` types; add `output_path` to `CMAReport` |

---

## Chunk 1: DB Migration + Schema + Excel Generator Service

### Task 1: DB Migration

**Files:**
- Create: `DOCS/Setup/phase7_migration.sql`

- [ ] **Step 1: Write the migration SQL**

```sql
-- Phase 7 migration: add output_path column to cma_reports
-- Run this in the Supabase SQL Editor before starting Phase 7.
--
-- cma_reports table after Phase 6:
--   id, client_id, title, status, document_ids, created_by, created_at, updated_at
--
-- Phase 7 adds:
--   output_path TEXT  — Supabase Storage path to generated .xlsm (set on completion)

ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS output_path TEXT;
```

- [ ] **Step 2: Run the migration in Supabase SQL Editor**

Log into the Supabase project (id: sjdzmkqfsehfpptxoxca, ap-southeast-2) → SQL Editor → paste and run the SQL above.

Expected: `ALTER TABLE` success, no errors.

---

### Task 2: Schema Updates

**Files:**
- Modify: `backend/app/models/schemas.py`

- [ ] **Step 1: Write the failing tests first**

In `backend/tests/test_excel_generator.py`, add schema import checks (will be used across generator tests):

```python
# At the top of test_excel_generator.py
from app.models.schemas import CMAReportResponse, GenerateTriggerResponse, DownloadUrlResponse
```

Running `docker compose exec backend python -c "from app.models.schemas import GenerateTriggerResponse"` should fail with `ImportError`.

- [ ] **Step 2: Add the new schemas to `schemas.py`**

Open `backend/app/models/schemas.py`. Add after the `AuditEntry` class at the bottom:

```python
# ── Phase 7: Excel Generation schemas ──────────────────────────────────────


class GenerateTriggerResponse(BaseModel):
    task_id: str
    report_id: str
    message: str


class DownloadUrlResponse(BaseModel):
    signed_url: str
    expires_in: int = 60
```

Also update `CMAReportResponse` to add the optional `output_path` field:

```python
class CMAReportResponse(BaseModel):
    id: str
    client_id: str
    title: str
    status: str
    document_ids: list[str]
    created_by: str
    output_path: str | None = None   # ← add this line
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 3: Verify import works**

```bash
docker compose exec backend python -c "from app.models.schemas import GenerateTriggerResponse, DownloadUrlResponse; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add DOCS/Setup/phase7_migration.sql backend/app/models/schemas.py
git commit -m "feat(phase-7): add DB migration + schema types for Excel generation"
```

---

### Task 3: ExcelGenerator Service — Pure Layer Tests (RED)

**Files:**
- Create: `backend/tests/test_excel_generator.py`

- [ ] **Step 1: Write all pure-layer failing tests**

Create `backend/tests/test_excel_generator.py`:

```python
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
from unittest.mock import MagicMock, call, patch

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
    """Financial year is written to row 9 of the corresponding YEAR_TO_COLUMN column."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2024, "nature": "audited"}]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=[])

    # 2024 → column 'C' → index 3
    assert ws.cell(row=9, column=3).value == 2024


def test_generator_fills_nature_of_financials():
    """Nature of financials ('audited'/'provisional') is written to row 10."""
    _, ws = _make_ws()
    gen = _make_generator()
    docs = [{"financial_year": 2025, "nature": "provisional"}]

    gen.fill_workbook(ws, client_name="Test Co", docs=docs, cell_data=[])

    # 2025 → column 'D' → index 4
    assert ws.cell(row=10, column=4).value == "provisional"


def test_generator_fills_pnl_domestic_sales_row_22():
    """'Domestic Sales' (PNL row 22) is filled for financial year 2024."""
    _, ws = _make_ws()
    gen = _make_generator()
    cell_data = [{"cma_field_name": "Domestic Sales", "financial_year": 2024, "amount": 500_000.0}]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    # 2024 → col C (index 3), row 22
    assert ws.cell(row=22, column=3).value == 500_000.0


def test_generator_fills_pnl_wages_row_45():
    """'Wages' (PNL row 45) is filled correctly."""
    _, ws = _make_ws()
    gen = _make_generator()
    cell_data = [{"cma_field_name": "Wages", "financial_year": 2023, "amount": 120_000.0}]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    # 2023 → col B (index 2), row 45
    assert ws.cell(row=45, column=2).value == 120_000.0


def test_generator_fills_bs_share_capital_row_116():
    """'Issued, Subscribed and Paid up' (BS row 116) is filled correctly."""
    _, ws = _make_ws()
    gen = _make_generator()
    cell_data = [
        {
            "cma_field_name": "Issued, Subscribed and Paid up",
            "financial_year": 2024,
            "amount": 1_000_000.0,
        }
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    assert ws.cell(row=116, column=3).value == 1_000_000.0


def test_generator_fills_bs_debtors_row_206():
    """'Domestic Receivables' (BS row 206) is filled correctly."""
    _, ws = _make_ws()
    gen = _make_generator()
    cell_data = [
        {"cma_field_name": "Domestic Receivables", "financial_year": 2025, "amount": 250_000.0}
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    # 2025 → col D (index 4)
    assert ws.cell(row=206, column=4).value == 250_000.0


def test_generator_maps_year_to_correct_column():
    """Each year maps to the correct Excel column per YEAR_TO_COLUMN."""
    _, ws = _make_ws()
    gen = _make_generator()

    year_to_expected_col = {2023: 2, 2024: 3, 2025: 4, 2026: 5}
    cell_data = [
        {"cma_field_name": "Domestic Sales", "financial_year": yr, "amount": 1.0}
        for yr in year_to_expected_col
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    for yr, col in year_to_expected_col.items():
        assert ws.cell(row=22, column=col).value == 1.0, f"Year {yr} → col {col} failed"


def test_generator_handles_multiple_years():
    """Data for different years lands in different columns."""
    _, ws = _make_ws()
    gen = _make_generator()
    cell_data = [
        {"cma_field_name": "Wages", "financial_year": 2024, "amount": 100.0},
        {"cma_field_name": "Wages", "financial_year": 2025, "amount": 200.0},
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    assert ws.cell(row=45, column=3).value == 100.0  # 2024 → col C
    assert ws.cell(row=45, column=4).value == 200.0  # 2025 → col D


def test_generator_sums_multiple_items_same_row():
    """Multiple line items mapping to the same (field_name, year) are summed."""
    _, ws = _make_ws()
    gen = _make_generator()
    cell_data = [
        {"cma_field_name": "Domestic Sales", "financial_year": 2024, "amount": 300_000.0},
        {"cma_field_name": "Domestic Sales", "financial_year": 2024, "amount": 200_000.0},
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    assert ws.cell(row=22, column=3).value == 500_000.0


def test_generator_does_not_overwrite_formula_cells():
    """Cells not in PNL_FIELD_TO_ROW / BS_FIELD_TO_ROW are left untouched."""
    _, ws = _make_ws()
    gen = _make_generator()

    # Row 21 is NOT in PNL_FIELD_TO_ROW (first mapping entry is row 22)
    ws.cell(row=21, column=2).value = "=SUM(B17:B20)"
    cell_data = [
        {"cma_field_name": "Domestic Sales", "financial_year": 2023, "amount": 999.0}
    ]

    gen.fill_workbook(ws, client_name="Test Co", docs=[], cell_data=cell_data)

    # Row 22 col B (2023) should be written
    assert ws.cell(row=22, column=2).value == 999.0
    # Row 21 formula should be UNTOUCHED
    assert ws.cell(row=21, column=2).value == "=SUM(B17:B20)"
```

- [ ] **Step 2: Run tests — confirm ALL fail with ImportError**

```bash
docker compose exec backend pytest tests/test_excel_generator.py -v 2>&1 | head -30
```

Expected: `ImportError: cannot import name 'ExcelGenerator'`

---

### Task 4: ExcelGenerator Service — Implementation (GREEN)

**Files:**
- Create: `backend/app/services/excel_generator.py`

- [ ] **Step 1: Write the implementation**

Create `backend/app/services/excel_generator.py`:

```python
"""CMA Excel generation service.

Fills the CMA.xlsm INPUT SHEET with classified financial data,
uploads the result to Supabase Storage, logs to audit trail,
and cleans up temp files.

Design
------
fill_workbook(ws, client_name, docs, cell_data)
    Pure transform: writes to an already-open worksheet.
    No DB calls, no file I/O — fully unit-testable.

generate(report_id, user_id) -> str
    Full pipeline: fetch data from DB, open template, fill,
    save temp file, upload, audit, cleanup.
    Returns the Supabase Storage path of the uploaded file.
"""

from __future__ import annotations

import logging
import os
import tempfile

import openpyxl
from openpyxl.utils import column_index_from_string

from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.mappings.year_columns import YEAR_TO_COLUMN
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_PATH = "/app/DOCS/CMA.xlsm"
STORAGE_BUCKET = "generated"
INPUT_SHEET_NAME = "INPUT SHEET"

# Header row constants (INPUT SHEET layout)
_ROW_CLIENT_NAME = 7
_ROW_FINANCIAL_YEAR = 9
_ROW_NATURE = 10


class ExcelGenerator:
    """Generates the CMA Excel file from reviewed classifications."""

    def __init__(self, service, template_path: str | None = None) -> None:
        self.service = service
        self.template_path = template_path or DEFAULT_TEMPLATE_PATH

    # ── Public API ────────────────────────────────────────────────────────

    def fill_workbook(
        self,
        ws,
        client_name: str,
        docs: list[dict],
        cell_data: list[dict],
    ) -> None:
        """Pure transform: fill *ws* (an open worksheet) with CMA data.

        Parameters
        ----------
        ws          — openpyxl Worksheet (INPUT SHEET)
        client_name — client name for the header row
        docs        — list of {"financial_year": int, "nature": str}
        cell_data   — list of {"cma_field_name": str, "financial_year": int, "amount": float}
        """
        self._fill_headers(ws, client_name, docs)
        self._fill_data_cells(ws, cell_data)

    def generate(self, report_id: str, user_id: str) -> str:
        """Full pipeline: fetch → fill → save → upload → audit → cleanup.

        Returns
        -------
        str — Supabase Storage path of the uploaded .xlsm file
        """
        logger.info("ExcelGenerator.generate started for report_id=%s", report_id)

        # 1. Fetch everything needed
        report = self._fetch_report(report_id)
        client_name = self._fetch_client_name(report["client_id"])
        doc_ids: list[str] = report.get("document_ids") or []
        docs = self._fetch_documents(doc_ids)
        cell_data = self._fetch_classified_data(doc_ids)

        # 2. Open template (keep_vba=True — MANDATORY for macros)
        wb = openpyxl.load_workbook(self.template_path, keep_vba=True)
        ws = wb[INPUT_SHEET_NAME]

        # 3. Fill worksheet
        self.fill_workbook(ws, client_name, docs, cell_data)

        # 4. Save, upload, cleanup
        storage_path = self._save_upload_cleanup(wb, report_id, user_id)

        logger.info(
            "ExcelGenerator.generate complete: report_id=%s path=%s",
            report_id,
            storage_path,
        )
        return storage_path

    # ── Private: fill helpers ─────────────────────────────────────────────

    def _fill_headers(self, ws, client_name: str, docs: list[dict]) -> None:
        ws.cell(row=_ROW_CLIENT_NAME, column=1).value = client_name
        for doc in docs:
            year = doc.get("financial_year")
            col_letter = YEAR_TO_COLUMN.get(year)
            if col_letter is None:
                continue
            col = column_index_from_string(col_letter)
            ws.cell(row=_ROW_FINANCIAL_YEAR, column=col).value = year
            ws.cell(row=_ROW_NATURE, column=col).value = doc.get("nature", "")

    def _fill_data_cells(self, ws, cell_data: list[dict]) -> None:
        """Accumulate amounts by (row, col) then write once per cell."""
        accumulator: dict[tuple[int, int], float] = {}

        for item in cell_data:
            field = item.get("cma_field_name")
            year = item.get("financial_year")
            amount = float(item.get("amount") or 0)

            row = ALL_FIELD_TO_ROW.get(field)
            col_letter = YEAR_TO_COLUMN.get(year)
            if row is None or col_letter is None:
                continue

            col = column_index_from_string(col_letter)
            key = (row, col)
            accumulator[key] = accumulator.get(key, 0.0) + amount

        for (row, col), value in accumulator.items():
            ws.cell(row=row, column=col).value = value

    # ── Private: I/O helpers ──────────────────────────────────────────────

    def _save_upload_cleanup(self, wb, report_id: str, user_id: str) -> str:
        """Save workbook to temp file, upload to Supabase Storage, cleanup."""
        storage_path = f"cma_reports/{report_id}/output.xlsm"
        tmp_path: str | None = None

        try:
            # mkstemp gives us a file descriptor + path; we close fd so openpyxl can write
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsm")
            os.close(tmp_fd)

            # Save — extension .xlsm preserves VBA/macro container
            wb.save(tmp_path)

            # Upload to Supabase Storage (bucket: generated)
            with open(tmp_path, "rb") as f:
                file_bytes = f.read()

            self.service.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=file_bytes,
                file_options={
                    "content-type": "application/vnd.ms-excel.sheet.macroenabled.12"
                },
            )

            # Audit log
            log_action(
                self.service,
                user_id,
                "excel_generated",
                "cma_report",
                report_id,
                after={"output_path": storage_path},
            )

            return storage_path

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # ── Private: DB fetch helpers ─────────────────────────────────────────

    def _fetch_report(self, report_id: str) -> dict:
        result = (
            self.service.table("cma_reports")
            .select("id,client_id,document_ids")
            .eq("id", report_id)
            .single()
            .execute()
        )
        if not result.data:
            raise ValueError(f"CMA report not found: {report_id}")
        return result.data

    def _fetch_client_name(self, client_id: str) -> str:
        result = (
            self.service.table("clients")
            .select("id,name")
            .eq("id", client_id)
            .single()
            .execute()
        )
        if not result.data:
            raise ValueError(f"Client not found: {client_id}")
        return result.data["name"]

    def _fetch_documents(self, document_ids: list[str]) -> list[dict]:
        if not document_ids:
            return []
        result = (
            self.service.table("documents")
            .select("id,financial_year,nature")
            .in_("id", document_ids)
            .execute()
        )
        return result.data or []

    def _fetch_classified_data(self, document_ids: list[str]) -> list[dict]:
        """Return [{cma_field_name, financial_year, amount}] for all non-doubt classifications."""
        if not document_ids:
            return []

        # Get all line items for these documents
        items_result = (
            self.service.table("extracted_line_items")
            .select("id,document_id,amount")
            .in_("document_id", document_ids)
            .execute()
        )
        items = {row["id"]: row for row in (items_result.data or [])}
        if not items:
            return []

        # Get document → financial_year mapping
        docs_result = (
            self.service.table("documents")
            .select("id,financial_year")
            .in_("id", document_ids)
            .execute()
        )
        doc_years = {
            doc["id"]: doc["financial_year"] for doc in (docs_result.data or [])
        }

        # Get all non-doubt classifications for these line items
        item_ids = list(items.keys())
        clf_result = (
            self.service.table("classifications")
            .select("line_item_id,cma_field_name")
            .in_("line_item_id", item_ids)
            .eq("is_doubt", False)
            .execute()
        )
        classifications = clf_result.data or []

        cell_data = []
        for clf in classifications:
            if not clf.get("cma_field_name"):
                continue
            item = items.get(clf["line_item_id"])
            if not item:
                continue
            year = doc_years.get(item["document_id"])
            if not year:
                continue
            cell_data.append(
                {
                    "cma_field_name": clf["cma_field_name"],
                    "financial_year": year,
                    "amount": item.get("amount") or 0.0,
                }
            )

        return cell_data
```

- [ ] **Step 2: Run pure-layer tests — confirm they pass**

```bash
docker compose exec backend pytest tests/test_excel_generator.py -v -k "fills or maps or handles or sums or does_not" 2>&1
```

Expected: all 11 pure-layer tests pass.

---

### Task 5: ExcelGenerator Integration Tests (keep_vba, save, upload, audit, cleanup)

**Files:**
- Modify: `backend/tests/test_excel_generator.py` (add integration tests)

- [ ] **Step 1: Add integration-layer tests (append to test file)**

```python
# ── Integration layer tests ────────────────────────────────────────────────
# These mock: openpyxl.load_workbook, service.storage, os.unlink, log_action


def _build_full_mock_service() -> MagicMock:
    """Builds a mock Supabase service with all needed chains pre-configured."""
    service = MagicMock()

    # cma_reports fetch
    report_row = {
        "id": "report-aaa",
        "client_id": "client-bbb",
        "document_ids": ["doc-ccc"],
    }
    # clients fetch
    client_row = {"id": "client-bbb", "name": "Test Client Ltd"}
    # documents fetch (for headers and year mapping)
    doc_row = {"id": "doc-ccc", "financial_year": 2024, "nature": "audited"}
    # line items
    item_row = {"id": "item-ddd", "document_id": "doc-ccc", "amount": 100.0}
    # classifications
    clf_row = {"line_item_id": "item-ddd", "cma_field_name": "Domestic Sales"}

    def table_side_effect(name: str):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.in_.return_value = chain
        chain.single.return_value = chain
        chain.update.return_value = chain

        data_map = {
            "cma_reports": report_row,
            "clients": client_row,
            "documents": doc_row,          # single() returns dict; in_() returns list
            "extracted_line_items": item_row,
            "classifications": clf_row,
        }
        raw = data_map.get(name)
        if isinstance(raw, dict):
            chain.execute.return_value = MagicMock(data=raw)
        else:
            chain.execute.return_value = MagicMock(data=[raw] if raw else [])
        return chain

    service.table.side_effect = table_side_effect

    # Storage mock
    storage_bucket = MagicMock()
    storage_bucket.upload.return_value = {"Key": "cma_reports/report-aaa/output.xlsm"}
    service.storage.from_.return_value = storage_bucket

    return service


def _make_mock_wb():
    """Minimal mock workbook + worksheet."""
    ws = MagicMock()
    ws.__getitem__ = MagicMock()
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
        gen.generate(report_id="report-aaa", user_id="user-xxx")

    mock_load.assert_called_once_with("/fake/CMA.xlsm", keep_vba=True)


def test_generator_preserves_macros():
    """Same as above: keep_vba=True ensures VBA/macros are retained."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        mock_load.return_value, _ = _make_mock_wb()
        gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
        gen.generate(report_id="report-aaa", user_id="user-xxx")

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
        gen.generate(report_id="report-aaa", user_id="user-xxx")

    assert saved_paths, "wb.save was never called"
    assert saved_paths[0].endswith(".xlsm"), f"Expected .xlsm, got: {saved_paths[0]}"


def test_generator_uploads_to_supabase_storage():
    """Generated file is uploaded to the 'generated' Supabase Storage bucket."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
        storage_path = gen.generate(report_id="report-aaa", user_id="user-xxx")

    # Verify storage.from_('generated') was called
    service.storage.from_.assert_called_with("generated")
    # Verify upload was called and the returned path is correct
    service.storage.from_().upload.assert_called_once()
    assert storage_path == "cma_reports/report-aaa/output.xlsm"


def test_generator_logs_audit_trail():
    """log_action is called after successful upload."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        with patch("app.services.excel_generator.log_action") as mock_log:
            gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
            gen.generate(report_id="report-aaa", user_id="user-xxx")

    mock_log.assert_called_once()
    args = mock_log.call_args[0]
    assert args[2] == "excel_generated"        # action
    assert args[3] == "cma_report"             # entity_type
    assert args[4] == "report-aaa"             # entity_id


def test_generator_cleans_up_temp_file():
    """Temp .xlsm file is deleted after upload, even on success."""
    service = _build_full_mock_service()

    with patch("app.services.excel_generator.openpyxl.load_workbook") as mock_load:
        wb_mock, _ = _make_mock_wb()
        mock_load.return_value = wb_mock

        with patch("app.services.excel_generator.os.unlink") as mock_unlink:
            # os.path.exists must return True so unlink is triggered
            with patch("app.services.excel_generator.os.path.exists", return_value=True):
                gen = ExcelGenerator(service=service, template_path="/fake/CMA.xlsm")
                gen.generate(report_id="report-aaa", user_id="user-xxx")

    mock_unlink.assert_called_once()
    unlinked = mock_unlink.call_args[0][0]
    assert unlinked.endswith(".xlsm"), f"Expected .xlsm cleanup, got: {unlinked}"
```

- [ ] **Step 2: Run ALL excel_generator tests**

```bash
docker compose exec backend pytest tests/test_excel_generator.py -v 2>&1
```

Expected: all 19 tests pass (`PASSED`).

- [ ] **Step 3: Check coverage**

```bash
docker compose exec backend pytest tests/test_excel_generator.py --cov=app/services/excel_generator --cov-report=term-missing 2>&1
```

Expected: 100% coverage on `excel_generator.py`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/excel_generator.py backend/tests/test_excel_generator.py
git commit -m "feat(phase-7): excel_generator service — fill_workbook + generate (19 tests, 100% coverage)"
```

---

## Chunk 2: ARQ Task + API Endpoints + Tests

### Task 6: ARQ Excel Task (RED → GREEN)

**Files:**
- Create: `backend/app/workers/excel_tasks.py`
- Create: `backend/tests/test_excel_tasks.py`
- Modify: `backend/app/workers/worker.py`

- [ ] **Step 1: Write failing task tests**

Create `backend/tests/test_excel_tasks.py`:

```python
"""Tests for run_excel_generation ARQ task."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_excel_task_calls_generator():
    """run_excel_generation calls ExcelGenerator.generate() with the report_id."""
    with patch("app.workers.excel_tasks.ExcelGenerator") as MockGen:
        instance = MagicMock()
        instance.generate.return_value = "cma_reports/rep-aaa/output.xlsm"
        MockGen.return_value = instance

        with patch("app.workers.excel_tasks.get_service_client") as mock_svc:
            mock_service = MagicMock()
            # mock the status update call
            mock_service.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
            mock_svc.return_value = mock_service

            from app.workers.excel_tasks import run_excel_generation

            result = await run_excel_generation({}, "rep-aaa")

    instance.generate.assert_called_once_with(report_id="rep-aaa", user_id="system")
    assert result["status"] == "complete"


@pytest.mark.asyncio
async def test_excel_task_updates_report_status_on_success():
    """On success, report status is updated to 'complete' with output_path."""
    with patch("app.workers.excel_tasks.ExcelGenerator") as MockGen:
        instance = MagicMock()
        instance.generate.return_value = "cma_reports/rep-aaa/output.xlsm"
        MockGen.return_value = instance

        with patch("app.workers.excel_tasks.get_service_client") as mock_svc:
            mock_service = MagicMock()
            update_chain = MagicMock()
            mock_service.table.return_value.update.return_value = update_chain
            update_chain.eq.return_value.execute.return_value = MagicMock(data=[{}])
            mock_svc.return_value = mock_service

            from app.workers.excel_tasks import run_excel_generation

            await run_excel_generation({}, "rep-aaa")

    # Verify update was called with status=complete and output_path
    update_call_args = mock_service.table.return_value.update.call_args[0][0]
    assert update_call_args["status"] == "complete"
    assert "output_path" in update_call_args


@pytest.mark.asyncio
async def test_excel_task_updates_report_status_on_failure():
    """On failure, report status is updated to 'failed' and the exception re-raised."""
    with patch("app.workers.excel_tasks.ExcelGenerator") as MockGen:
        instance = MagicMock()
        instance.generate.side_effect = RuntimeError("template missing")
        MockGen.return_value = instance

        with patch("app.workers.excel_tasks.get_service_client") as mock_svc:
            mock_service = MagicMock()
            update_chain = MagicMock()
            mock_service.table.return_value.update.return_value = update_chain
            update_chain.eq.return_value.execute.return_value = MagicMock(data=[{}])
            mock_svc.return_value = mock_service

            from app.workers.excel_tasks import run_excel_generation

            with pytest.raises(RuntimeError, match="template missing"):
                await run_excel_generation({}, "rep-aaa")

    # Verify status was set to 'failed'
    update_call_args = mock_service.table.return_value.update.call_args[0][0]
    assert update_call_args["status"] == "failed"
```

- [ ] **Step 2: Run — confirm ImportError (RED)**

```bash
docker compose exec backend pytest tests/test_excel_tasks.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'run_excel_generation'`

- [ ] **Step 3: Create `excel_tasks.py`**

Create `backend/app/workers/excel_tasks.py`:

```python
"""Background Excel generation task for the ARQ task queue."""

from __future__ import annotations

import logging

from app.dependencies import get_service_client
from app.services.excel_generator import ExcelGenerator

logger = logging.getLogger(__name__)


async def run_excel_generation(ctx: dict, report_id: str) -> dict:
    """ARQ task: generate CMA Excel for a report.

    Flow
    ----
    1. Call ExcelGenerator.generate() — fills template, uploads to storage.
    2. On success: update report status → 'complete', store output_path.
    3. On failure: update report status → 'failed', re-raise.

    Returns
    -------
    dict — {"report_id": str, "status": "complete", "path": str}

    Raises
    ------
    Exception — any exception from the generator (after setting status='failed')
    """
    service = get_service_client()
    logger.info("run_excel_generation started for report_id=%s", report_id)

    try:
        generator = ExcelGenerator(service=service)
        storage_path = generator.generate(report_id=report_id, user_id="system")

        service.table("cma_reports").update(
            {"status": "complete", "output_path": storage_path}
        ).eq("id", report_id).execute()

        logger.info(
            "run_excel_generation complete: report_id=%s path=%s",
            report_id,
            storage_path,
        )
        return {"report_id": report_id, "status": "complete", "path": storage_path}

    except Exception as exc:
        logger.error(
            "run_excel_generation failed: report_id=%s error=%s", report_id, exc
        )
        service.table("cma_reports").update({"status": "failed"}).eq(
            "id", report_id
        ).execute()
        raise
```

- [ ] **Step 4: Register task in worker**

Open `backend/app/workers/worker.py`. Change:

```python
from app.workers.classification_tasks import run_classification
from app.workers.extraction_tasks import run_extraction
```

to:

```python
from app.workers.classification_tasks import run_classification
from app.workers.excel_tasks import run_excel_generation
from app.workers.extraction_tasks import run_extraction
```

And change:

```python
    functions = [run_extraction, run_classification]
```

to:

```python
    functions = [run_extraction, run_classification, run_excel_generation]
```

- [ ] **Step 5: Run task tests — all pass (GREEN)**

```bash
docker compose exec backend pytest tests/test_excel_tasks.py -v 2>&1
```

Expected: 3 tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/app/workers/excel_tasks.py backend/app/workers/worker.py backend/tests/test_excel_tasks.py
git commit -m "feat(phase-7): ARQ run_excel_generation task — calls generator, manages status (3 tests)"
```

---

### Task 7: API Endpoints — Generate + Download (RED → GREEN)

**Files:**
- Modify: `backend/app/routers/cma_reports.py`
- Modify: `backend/tests/test_cma_reports.py`

- [ ] **Step 1: Write failing API endpoint tests**

Open `backend/tests/test_cma_reports.py`. Append these tests:

```python
# ── Phase 7: Generate + Download endpoint tests ────────────────────────────

REPORT_ID_GEN = "report-gen-0001"
STORAGE_PATH = f"cma_reports/{REPORT_ID_GEN}/output.xlsm"
SIGNED_URL = "https://storage.example.com/signed-url?token=abc"

_REPORT_COMPLETE = {
    "id": REPORT_ID_GEN,
    "client_id": CLIENT_ID,
    "title": "Phase 7 Report",
    "status": "complete",
    "document_ids": [DOC_ID_1],
    "created_by": "admin-uuid-0001",
    "output_path": STORAGE_PATH,
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}

_REPORT_DRAFT = {
    "id": REPORT_ID_GEN,
    "client_id": CLIENT_ID,
    "title": "Phase 7 Report",
    "status": "draft",
    "document_ids": [DOC_ID_1],
    "created_by": "admin-uuid-0001",
    "output_path": None,
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}


def test_generate_returns_202_when_no_doubts(admin_client):
    """POST /generate enqueues job and returns 202 when all doubts are resolved."""
    with patch("app.routers.cma_reports.get_service_client") as mock_svc, \
         patch("app.routers.cma_reports.create_pool") as mock_pool:

        svc = MagicMock()
        mock_svc.return_value = svc

        # report fetch
        svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=_REPORT_DRAFT)
        # line items
        svc.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[{"id": ITEM_ID_1}])
        # doubt count → 0 doubts
        svc.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        # status update
        svc.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[_REPORT_DRAFT])

        # Mock ARQ pool
        redis_mock = AsyncMock()
        job_mock = MagicMock()
        job_mock.job_id = "task-gen-001"
        redis_mock.enqueue_job = AsyncMock(return_value=job_mock)
        redis_mock.aclose = AsyncMock()
        mock_pool.return_value.__aenter__ = AsyncMock(return_value=redis_mock)
        mock_pool.return_value = redis_mock

        resp = admin_client.post(f"/api/cma-reports/{REPORT_ID_GEN}/generate")

    assert resp.status_code == 202
    body = resp.json()
    assert body["report_id"] == REPORT_ID_GEN
    assert "task_id" in body


def test_generate_blocked_if_doubts_unresolved(admin_client):
    """POST /generate returns 400 when unresolved doubts exist."""
    with patch("app.routers.cma_reports.get_service_client") as mock_svc:
        svc = MagicMock()
        mock_svc.return_value = svc

        # report fetch
        svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=_REPORT_DRAFT)
        # line items
        svc.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[{"id": ITEM_ID_1}])
        # doubt count → 2 doubts remain
        svc.table.return_value.select.return_value.in_.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "clf-doubt-1"}, {"id": "clf-doubt-2"}]
        )

        resp = admin_client.post(f"/api/cma-reports/{REPORT_ID_GEN}/generate")

    assert resp.status_code == 400
    assert "doubt" in resp.json()["detail"].lower()


def test_download_returns_signed_url(admin_client):
    """GET /download returns a signed URL for the generated file."""
    with patch("app.routers.cma_reports.get_service_client") as mock_svc:
        svc = MagicMock()
        mock_svc.return_value = svc

        # report fetch — status=complete, output_path set
        svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=_REPORT_COMPLETE)
        # storage signed URL
        svc.storage.from_.return_value.create_signed_url.return_value = {
            "signedURL": SIGNED_URL
        }

        resp = admin_client.get(f"/api/cma-reports/{REPORT_ID_GEN}/download")

    assert resp.status_code == 200
    body = resp.json()
    assert body["signed_url"] == SIGNED_URL
    assert body["expires_in"] == 60


def test_download_404_when_not_generated(admin_client):
    """GET /download returns 404 if the report has no output_path yet."""
    with patch("app.routers.cma_reports.get_service_client") as mock_svc:
        svc = MagicMock()
        mock_svc.return_value = svc

        # report fetch — output_path is None
        svc.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data=_REPORT_DRAFT)

        resp = admin_client.get(f"/api/cma-reports/{REPORT_ID_GEN}/download")

    assert resp.status_code == 404
```

- [ ] **Step 2: Run — confirm failures (RED)**

```bash
docker compose exec backend pytest tests/test_cma_reports.py -v -k "generate or download" 2>&1 | tail -20
```

Expected: 404s or similar failures.

- [ ] **Step 3: Add endpoints to `cma_reports.py`**

Open `backend/app/routers/cma_reports.py`. At the top, add imports:

```python
from arq import create_pool

from app.models.schemas import (
    AuditEntry,
    CMAReportCreate,
    CMAReportResponse,
    ClassificationResponse,
    ConfidenceSummary,
    DownloadUrlResponse,
    GenerateTriggerResponse,
    UserProfile,
)
from app.workers.worker import _get_redis_settings
```

(Replace the existing `from app.models.schemas import (...)` block entirely with the above.)

Then append these two endpoints at the end of `cma_reports.py`:

```python
# ── Generate Excel ─────────────────────────────────────────────────────────


@router.post(
    "/cma-reports/{report_id}/generate",
    response_model=GenerateTriggerResponse,
    status_code=202,
)
async def generate_cma_excel(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> GenerateTriggerResponse:
    """Enqueue Excel generation. Blocked if any is_doubt=True classifications remain."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)

    # Guard: block if any unresolved doubts exist
    document_ids = report.get("document_ids") or []
    item_ids = _get_report_item_ids(service, document_ids)
    if item_ids:
        doubt_result = (
            service.table("classifications")
            .select("id")
            .in_("line_item_id", item_ids)
            .eq("is_doubt", True)
            .execute()
        )
        doubts = doubt_result.data or []
        if doubts:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot generate: {len(doubts)} unresolved doubt(s) remain. "
                    "Resolve all doubts before generating the Excel file."
                ),
            )

    # Update status → generating
    service.table("cma_reports").update({"status": "generating"}).eq(
        "id", report_id
    ).execute()

    # Enqueue ARQ task
    redis_settings = _get_redis_settings()
    redis_pool = await create_pool(redis_settings)
    try:
        job = await redis_pool.enqueue_job("run_excel_generation", report_id)
    finally:
        await redis_pool.aclose()

    logger.info(
        "Enqueued Excel generation for report_id=%s task_id=%s",
        report_id,
        job.job_id,
    )

    return GenerateTriggerResponse(
        task_id=job.job_id,
        report_id=report_id,
        message="Excel generation queued.",
    )


# ── Download signed URL ────────────────────────────────────────────────────


@router.get(
    "/cma-reports/{report_id}/download",
    response_model=DownloadUrlResponse,
)
async def download_cma_excel(
    report_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> DownloadUrlResponse:
    """Return a 60-second signed Supabase Storage URL for the generated .xlsm."""
    service = get_service_client()
    report = _get_owned_report(service, report_id, current_user)

    output_path: str | None = report.get("output_path")
    if not output_path:
        raise HTTPException(
            status_code=404,
            detail="Excel file not yet generated. Trigger generation first.",
        )

    result = service.storage.from_("generated").create_signed_url(
        path=output_path, expires_in=60
    )
    signed_url: str = result["signedURL"]

    return DownloadUrlResponse(signed_url=signed_url, expires_in=60)
```

- [ ] **Step 4: Run endpoint tests (GREEN)**

```bash
docker compose exec backend pytest tests/test_cma_reports.py -v -k "generate or download" 2>&1
```

Expected: all 4 new tests pass.

- [ ] **Step 5: Run full backend test suite**

```bash
docker compose exec backend pytest --tb=short 2>&1 | tail -20
```

Expected: 255 existing tests + 26 new tests (19 excel_generator + 3 excel_tasks + 4 cma_reports) = 278+ passing, 0 failing.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/cma_reports.py backend/tests/test_cma_reports.py
git commit -m "feat(phase-7): add /generate + /download API endpoints with doubt guard (4 tests)"
```

---

## Chunk 3: Frontend — Generate Page + Enable Button

### Task 8: Types Update

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Add Phase 7 types**

Open `frontend/src/types/index.ts`. Add `output_path` to `CMAReport` and append the new response types at the bottom:

Change:
```typescript
export interface CMAReport {
  id: string;
  client_id: string;
  title: string;
  status: CMAReportStatus;
  document_ids: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
}
```

To:
```typescript
export interface CMAReport {
  id: string;
  client_id: string;
  title: string;
  status: CMAReportStatus;
  document_ids: string[];
  created_by: string;
  output_path: string | null;
  created_at: string;
  updated_at: string;
}
```

Append at the bottom of `types/index.ts`:
```typescript
// ── Phase 7: Excel Generation ─────────────────────────────────────────────

export interface GenerateTriggerResponse {
  task_id: string;
  report_id: string;
  message: string;
}

export interface DownloadUrlResponse {
  signed_url: string;
  expires_in: number;
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
docker compose exec frontend npx tsc --noEmit 2>&1
```

Expected: no errors.

---

### Task 9: Enable "Generate Excel" Button on Overview Page

**Files:**
- Modify: `frontend/src/app/(app)/cma/[id]/page.tsx`

- [ ] **Step 1: Replace the disabled button**

Open `frontend/src/app/(app)/cma/[id]/page.tsx`.

Replace:
```tsx
          <Button
            size="sm"
            disabled
            title="Complete review first — available in Phase 7"
          >
            <FileBarChart className="mr-1.5 h-4 w-4" />
            Generate Excel
          </Button>
```

With:
```tsx
          {allReviewed ? (
            <Link href={`/cma/${reportId}/generate`}>
              <Button size="sm">
                <FileBarChart className="mr-1.5 h-4 w-4" />
                Generate Excel
              </Button>
            </Link>
          ) : (
            <Button
              size="sm"
              disabled
              title={
                summary.needs_review > 0
                  ? `Resolve ${summary.needs_review} doubt(s) first`
                  : "Complete review first"
              }
            >
              <FileBarChart className="mr-1.5 h-4 w-4" />
              Generate Excel
            </Button>
          )}
```

- [ ] **Step 2: Remove the "ready to generate" banner** (it's now redundant — the button is enabled)

Remove these lines from `page.tsx`:
```tsx
      {allReviewed && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950/20">
          <p className="text-sm font-medium text-green-800 dark:text-green-300">
            All items reviewed — ready to generate Excel (Phase 7).
          </p>
        </div>
      )}
```

- [ ] **Step 3: Verify TypeScript**

```bash
docker compose exec frontend npx tsc --noEmit 2>&1
```

Expected: no errors.

---

### Task 10: Generate Progress Page

**Files:**
- Create: `frontend/src/app/(app)/cma/[id]/generate/page.tsx`

- [ ] **Step 1: Write the implementation**

Create `frontend/src/app/(app)/cma/[id]/generate/page.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle,
  Download,
  FileBarChart,
  Loader2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import type { CMAReport, DownloadUrlResponse, GenerateTriggerResponse } from "@/types";

type GenerateState = "idle" | "starting" | "generating" | "complete" | "failed";

export default function GeneratePage() {
  const { id: reportId } = useParams<{ id: string }>();
  const router = useRouter();

  const [state, setState] = useState<GenerateState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Kick off generation on mount
  useEffect(() => {
    if (!reportId) return;
    startGeneration();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId]);

  async function startGeneration() {
    setState("starting");
    try {
      await apiClient<GenerateTriggerResponse>(
        `/api/cma-reports/${reportId}/generate`,
        { method: "POST" }
      );
      setState("generating");
      startPolling();
    } catch (err) {
      setState("failed");
      setErrorMsg(err instanceof Error ? err.message : "Failed to start generation");
    }
  }

  function startPolling() {
    pollRef.current = setInterval(async () => {
      try {
        const report = await apiClient<CMAReport>(`/api/cma-reports/${reportId}`);
        if (report.status === "complete") {
          clearInterval(pollRef.current!);
          setState("complete");
        } else if (report.status === "failed") {
          clearInterval(pollRef.current!);
          setState("failed");
          setErrorMsg("Excel generation failed. Please try again.");
        }
      } catch {
        // ignore transient errors — keep polling
      }
    }, 2000);
  }

  async function handleDownload() {
    try {
      const { signed_url } = await apiClient<DownloadUrlResponse>(
        `/api/cma-reports/${reportId}/download`
      );
      window.open(signed_url, "_blank");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Download failed");
    }
  }

  async function handleRetry() {
    setErrorMsg(null);
    await startGeneration();
  }

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <Link
        href={`/cma/${reportId}`}
        className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Report
      </Link>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileBarChart className="h-5 w-5" />
            Generate CMA Excel
          </CardTitle>
          <CardDescription>
            Filling the CMA template with classified financial data.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {(state === "starting" || state === "generating") && (
            <div className="flex flex-col items-center gap-3 py-6">
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {state === "starting"
                  ? "Starting generation…"
                  : "Generating Excel file — this may take a few seconds…"}
              </p>
            </div>
          )}

          {state === "complete" && (
            <div className="flex flex-col items-center gap-4 py-6">
              <CheckCircle className="h-10 w-10 text-green-500" />
              <p className="text-sm font-medium">CMA Excel is ready!</p>
              <Button onClick={handleDownload} size="sm">
                <Download className="mr-1.5 h-4 w-4" />
                Download .xlsm
              </Button>
              <p className="text-xs text-muted-foreground">
                The download link expires in 60 seconds. Click again to get a new link.
              </p>
            </div>
          )}

          {state === "failed" && (
            <div className="flex flex-col items-center gap-4 py-6">
              <XCircle className="h-10 w-10 text-destructive" />
              <p className="text-sm font-medium text-destructive">
                {errorMsg ?? "Generation failed."}
              </p>
              <Button variant="outline" size="sm" onClick={handleRetry}>
                Retry
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
docker compose exec frontend npx tsc --noEmit 2>&1
```

Expected: no errors.

- [ ] **Step 3: Commit frontend**

```bash
git add frontend/src/types/index.ts \
        frontend/src/app/\(app\)/cma/\[id\]/page.tsx \
        frontend/src/app/\(app\)/cma/\[id\]/generate/page.tsx
git commit -m "feat(phase-7): generate progress page + enable Generate Excel button"
```

---

## Final Verification

- [ ] **Run full backend test suite**

```bash
docker compose exec backend pytest --cov=app --cov-report=term-missing 2>&1 | tail -30
```

Expected: 278+ tests, 0 failures, overall coverage ≥ 80%, `excel_generator.py` = 100%.

- [ ] **Frontend build check**

```bash
docker compose exec frontend npm run build 2>&1 | tail -20
```

Expected: build succeeds, no TypeScript errors.

- [ ] **Smoke test (manual, with Docker running)**

1. Navigate to a CMA report with 0 doubts → "Generate Excel" button is enabled and links to `/cma/{id}/generate`
2. Navigate to a report with unresolved doubts → button is disabled with tooltip
3. Click "Generate Excel" → spinner appears, polls status
4. Wait for completion → "Download .xlsm" button appears
5. Click download → `.xlsm` file opens from signed URL

---

## Commit Sequence Summary

| Commit | Files |
|--------|-------|
| `feat(phase-7): add DB migration + schema types` | `phase7_migration.sql`, `schemas.py` |
| `feat(phase-7): excel_generator service (19 tests, 100% coverage)` | `excel_generator.py`, `test_excel_generator.py` |
| `feat(phase-7): ARQ run_excel_generation task (3 tests)` | `excel_tasks.py`, `worker.py`, `test_excel_tasks.py` |
| `feat(phase-7): add /generate + /download API endpoints (4 tests)` | `cma_reports.py`, `test_cma_reports.py` |
| `feat(phase-7): generate progress page + enable Generate Excel button` | `types/index.ts`, `cma/[id]/page.tsx`, `cma/[id]/generate/page.tsx` |
