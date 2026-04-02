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

import logging
import re
from io import BytesIO

import pdfplumber

from app.services.extraction._types import ExtractionError, LineItem, parse_amount

logger = logging.getLogger(__name__)

# ── Header detection ─────────────────────────────────────────────────────────

# Column headers we want to skip in tables
_HEADER_PATTERNS = re.compile(
    r"^\s*(description|particulars|item|amount|rs\.?|inr|₹|sr\.?\s*no\.?|"
    r"note\s*no\.?|schedule|as\s+at|for\s+the\s+year|total|balance\s+sheet|"
    r"profit\s+and\s+loss|statement\s+of)\s*$",
    re.IGNORECASE,
)

# Text-line pattern: "Label text    1,23,456" or "Label text    (1,23,456)"
# Amount must be at the end, preceded by whitespace (1+ spaces for flexibility)
# Also handles negative amounts in parentheses: (1,23,456)
_TEXT_LINE_RE = re.compile(
    r"^(.+?)\s{2,}(\(?\s*[\d,]+\.?\d*\s*\)?)\s*$"
)

# Fallback pattern with single space + tab separation (common in CA PDFs)
_TEXT_LINE_FALLBACK_RE = re.compile(
    r"^(.+?)\s+(\(?\s*[\d,]{3,}[\d,.]*\s*\)?)\s*$"
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
                logger.info("PDF opened: %d pages", len(pdf.pages))
                for page_idx, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    if tables:
                        table_items = self._parse_tables(tables)
                        logger.info(
                            "Page %d: found %d tables, extracted %d items from tables",
                            page_idx, len(tables), len(table_items),
                        )
                        items.extend(table_items)
                    else:
                        text = page.extract_text()
                        if text:
                            text_items = self._parse_text(text)
                            logger.info(
                                "Page %d: no tables, parsed text (%d chars) → %d items",
                                page_idx, len(text), len(text_items),
                            )
                            items.extend(text_items)
                            if len(text_items) == 0 and len(text.strip()) > 50:
                                # Log first 200 chars to help debug why parsing failed
                                logger.debug(
                                    "Page %d: text sample (first 200 chars): %s",
                                    page_idx, text[:200].replace("\n", " | "),
                                )
                        else:
                            logger.info("Page %d: no tables and no extractable text", page_idx)

            if len(items) == 0:
                logger.warning(
                    "PdfExtractor: 0 items extracted from %d-page PDF. "
                    "This PDF may have an unusual format or be image-based "
                    "despite having minimal text layer.",
                    len(pdf.pages) if hasattr(pdf, 'pages') else -1,
                )

            return items
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Failed to extract PDF: {e}") from e

    # ── Table parsing ─────────────────────────────────────────────────────────

    def _parse_tables(self, tables: list) -> list[LineItem]:
        """Convert pdfplumber table rows into LineItems."""
        items: list[LineItem] = []

        for table_idx, table in enumerate(tables):
            if not table:
                continue

            current_section = ""
            skipped_rows = 0
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

                # Find numeric amount — scan ALL cells after the first (description) cell.
                # Indian CA statements sometimes have Note No, Current Year, Previous Year columns.
                # We want the LAST parseable amount (often the current year column is rightmost).
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
                        # Take the FIRST valid amount (typically the current year)
                        break

                if amount is None:
                    # No amount → possible section header
                    if description == description.upper() and any(c.isalpha() for c in description):
                        current_section = description.lower()
                    else:
                        skipped_rows += 1
                    continue

                items.append(
                    LineItem(
                        description=description,
                        amount=amount,
                        section=current_section,
                        raw_text=f"{description}  {raw_amount}",
                    )
                )

            if skipped_rows > 0:
                logger.debug(
                    "Table %d: skipped %d rows without parseable amounts",
                    table_idx, skipped_rows,
                )

        return items

    # ── Text parsing ──────────────────────────────────────────────────────────

    def _parse_text(self, text: str) -> list[LineItem]:
        """
        Parse free-form text lines of the form:
          "Label text    1,23,456"
          "Label text    (1,23,456)"     ← negative (Indian accounting)

        Uses two-or-more spaces as the primary separator.
        Falls back to single-space separator if the primary yields nothing.
        """
        items: list[LineItem] = []
        current_section = ""

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            # Try primary pattern (2+ space separator) first
            match = _TEXT_LINE_RE.match(line)
            if not match:
                # Try fallback (1+ space, but amount must be 3+ digits to avoid false positives)
                match = _TEXT_LINE_FALLBACK_RE.match(line)
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

            # Skip if description looks like a pure number or header
            if _is_header_cell(description):
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
