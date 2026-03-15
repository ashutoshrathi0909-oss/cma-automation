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
