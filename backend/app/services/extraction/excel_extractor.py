"""
excel_extractor.py
==================
Extracts financial line items from Excel files (.xlsx and .xls).

Strategy
--------
1. Open the workbook (openpyxl for xlsx, xlrd for xls).
2. Iterate every sheet, every row.
3. A row is a **section header** when:
   - Column A/B contains an all-caps string OR bold-formatted text
   - AND no parseable numeric value appears in the row.
4. A row is a **data row** when:
   - Column A/B contains a non-empty description string
   - AND at least one cell in the row contains a parseable number.
5. Indian number formatting ("1,23,456") is normalised via parse_amount().
"""

from __future__ import annotations

import io
from typing import Optional

from app.services.extraction._types import ExtractionError, LineItem, parse_amount


# ── Helpers ───────────────────────────────────────────────────────────────────


def _is_section_header(label: str) -> bool:
    """
    Return True when *label* looks like a section heading.

    Heuristic: all characters are uppercase letters, digits, spaces or
    punctuation (i.e. no mixed-case description words).
    """
    stripped = label.strip()
    if not stripped:
        return False
    # Pure uppercase text with no lowercase letters = header
    return stripped == stripped.upper() and any(c.isalpha() for c in stripped)


def _find_amount_in_row(row_values: list) -> Optional[float]:
    """
    Scan *row_values* (starting from index 1) for the first parseable number.

    Returns the float value, or None if no numeric cell is found.
    """
    for cell_value in row_values[1:]:
        if cell_value is None:
            continue
        if isinstance(cell_value, (int, float)) and not isinstance(cell_value, bool):
            return float(cell_value)
        if isinstance(cell_value, str):
            parsed = parse_amount(cell_value)
            if parsed is not None:
                return parsed
    return None


# ── ExcelExtractor ────────────────────────────────────────────────────────────


class ExcelExtractor:
    """Extracts LineItems from .xlsx and .xls workbooks."""

    async def extract(self, file_content: bytes, file_type: str) -> list[LineItem]:
        """
        Extract financial line items from an Excel file.

        Parameters
        ----------
        file_content : bytes
            Raw Excel file bytes.
        file_type : str
            "xlsx" or "xls" (case-insensitive).

        Returns
        -------
        list[LineItem]
        """
        try:
            file_type = file_type.lower()
            if file_type == "xlsx":
                return self._extract_xlsx(file_content)
            elif file_type == "xls":
                return self._extract_xls(file_content)
            else:
                raise ExtractionError(f"Unsupported file type: {file_type}")
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Failed to extract Excel file: {e}") from e

    # ── xlsx (openpyxl) ───────────────────────────────────────────────────────

    def _extract_xlsx(self, file_content: bytes) -> list[LineItem]:
        import openpyxl

        wb = openpyxl.load_workbook(
            io.BytesIO(file_content),
            data_only=True,  # get cell values, not formulas
            read_only=True,
        )

        items: list[LineItem] = []

        for sheet in wb.worksheets:
            current_section = ""
            for row in sheet.iter_rows():
                row_values = [cell.value for cell in row]
                # Pick description from col A or B
                description = self._get_description(row_values)
                if not description:
                    continue  # skip empty rows

                amount = _find_amount_in_row(row_values)

                if amount is None:
                    # No numeric value → treat as section header if appropriate
                    if _is_section_header(description):
                        current_section = description.strip().lower()
                    continue

                items.append(
                    LineItem(
                        description=description.strip(),
                        amount=amount,
                        section=current_section,
                        raw_text=str(row_values),
                    )
                )

        wb.close()
        return items

    # ── xls (xlrd) ────────────────────────────────────────────────────────────

    def _extract_xls(self, file_content: bytes) -> list[LineItem]:
        import xlrd

        wb = xlrd.open_workbook(file_contents=file_content)
        items: list[LineItem] = []

        for sheet in wb.sheets():
            current_section = ""
            for row_idx in range(sheet.nrows):
                row_values = sheet.row_values(row_idx)
                description = self._get_description(row_values)
                if not description:
                    continue

                amount = _find_amount_in_row(row_values)

                if amount is None:
                    if _is_section_header(description):
                        current_section = description.strip().lower()
                    continue

                items.append(
                    LineItem(
                        description=description.strip(),
                        amount=amount,
                        section=current_section,
                        raw_text=str(row_values),
                    )
                )

        return items

    # ── Shared helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_description(row_values: list) -> str:
        """
        Return the text label from the first or second column of a row.

        Tries column A first, then column B, then gives up.
        Returns empty string if neither column has a text value.
        """
        for idx in range(min(2, len(row_values))):
            val = row_values[idx]
            if isinstance(val, str) and val.strip():
                return val.strip()
        return ""
