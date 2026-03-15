"""
pdf_extractor.py
================
Extracts financial line items from native (text-based) PDFs.

Strategy
--------
1. Open the PDF with pdfplumber.
2. For each page, attempt table extraction first.
3. If no tables are found on a page, fall back to plain text parsing.
4. Skip header rows (where the second column is non-numeric / looks like "Amount").
5. Normalise amounts via parse_amount() (handles Indian + Western formats).
"""

from __future__ import annotations

import re
from io import BytesIO

import pdfplumber

from app.services.extraction._types import ExtractionError, LineItem, parse_amount


# ── Header detection ─────────────────────────────────────────────────────────

# Column headers we want to skip in tables
_HEADER_PATTERNS = re.compile(
    r"^\s*(description|particulars|item|amount|rs\.?|inr|₹|sr\.?\s*no\.?)\s*$",
    re.IGNORECASE,
)

# Text-line pattern: "Label text    1,23,456"
# Amount must be at the end, preceded by whitespace
_TEXT_LINE_RE = re.compile(
    r"^(.+?)\s{2,}([\d,]+\.?\d*)\s*$"
)


def _is_header_cell(value: str) -> bool:
    """Return True if *value* looks like a column header rather than data."""
    if not isinstance(value, str):
        return False
    return bool(_HEADER_PATTERNS.match(value.strip()))


# ── PdfExtractor ──────────────────────────────────────────────────────────────


class PdfExtractor:
    """Extracts LineItems from native (text-layer) PDFs using pdfplumber."""

    async def extract(self, file_content: bytes) -> list[LineItem]:
        """
        Extract financial line items from a PDF with a text layer.

        Parameters
        ----------
        file_content : bytes
            Raw PDF bytes.

        Returns
        -------
        list[LineItem]
        """
        try:
            items: list[LineItem] = []

            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        items.extend(self._parse_tables(tables))
                    else:
                        text = page.extract_text()
                        if text:
                            items.extend(self._parse_text(text))

            return items
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Failed to extract PDF: {e}") from e

    # ── Table parsing ─────────────────────────────────────────────────────────

    def _parse_tables(self, tables: list) -> list[LineItem]:
        """Convert pdfplumber table rows into LineItems."""
        items: list[LineItem] = []

        for table in tables:
            if not table:
                continue

            current_section = ""
            for row in table:
                if not row:
                    continue

                # Determine description (first non-None cell)
                description = ""
                for cell in row:
                    if cell and isinstance(cell, str) and cell.strip():
                        description = cell.strip()
                        break

                if not description:
                    continue

                # Skip rows where ALL cells look like header labels
                if all(
                    not cell or _is_header_cell(str(cell))
                    for cell in row
                    if cell
                ):
                    continue

                # Find numeric amount (skip description cell and header cells)
                amount: float | None = None
                raw_amount = ""
                for cell in row[1:]:
                    if cell is None:
                        continue
                    cell_str = str(cell).strip()
                    if not cell_str or _is_header_cell(cell_str):
                        continue
                    parsed = parse_amount(cell_str)
                    if parsed is not None:
                        amount = parsed
                        raw_amount = cell_str
                        break

                if amount is None:
                    # No amount → possible section header
                    if description == description.upper() and any(c.isalpha() for c in description):
                        current_section = description.lower()
                    continue

                items.append(
                    LineItem(
                        description=description,
                        amount=amount,
                        section=current_section,
                        raw_text=f"{description}  {raw_amount}",
                    )
                )

        return items

    # ── Text parsing ──────────────────────────────────────────────────────────

    def _parse_text(self, text: str) -> list[LineItem]:
        """
        Parse free-form text lines of the form:
          "Label text    1,23,456"

        Uses two-or-more spaces as the separator between label and amount.
        """
        items: list[LineItem] = []
        current_section = ""

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            match = _TEXT_LINE_RE.match(line)
            if not match:
                # No amount on this line — check if it's a section header
                if line == line.upper() and any(c.isalpha() for c in line):
                    current_section = line.lower()
                continue

            description = match.group(1).strip()
            raw_amount = match.group(2).strip()
            amount = parse_amount(raw_amount)

            if amount is None or not description:
                continue

            items.append(
                LineItem(
                    description=description,
                    amount=amount,
                    section=current_section,
                    raw_text=line,
                )
            )

        return items
