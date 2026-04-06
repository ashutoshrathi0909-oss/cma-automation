"""
excel_extractor.py
==================
Extracts financial line items from Excel files (.xlsx and .xls).

Strategy
--------
1. Open the workbook (openpyxl for xlsx, xlrd for xls).
2. Filter sheets: only process financial summary sheets (P&L, Balance
   Sheet, Notes, etc.).  Skip ledger / subsidiary / report sheets.
3. A row is a **section header** when:
   - Column A/B contains an all-caps string OR bold-formatted text
   - AND no parseable numeric value appears in the row.
4. A row is a **data row** when:
   - Column A/B contains a non-empty description string
   - AND at least one cell in the row contains a parseable number.
5. Indian number formatting ("1,23,456") is normalised via parse_amount().
6. Safety net: if a single sheet yields >300 items it is likely a
   ledger/transaction dump and is discarded with a warning.
"""

from __future__ import annotations

import io
import logging
import re
from difflib import SequenceMatcher
from typing import Optional

from app.services.extraction._types import ExtractionError, LineItem, normalize_line_text, parse_amount

logger = logging.getLogger(__name__)

# ── Sheet filtering ──────────────────────────────────────────────────────────

# Sheets whose names match these patterns are ALWAYS included.
# Covers: BS, P&L, Cash Flow, Notes, Depreciation.
# NOTE: Subnotes EXCLUDED — they contain vendor subledger detail, not summary data.
# NOTE: Trial Balance EXCLUDED — it's a ledger dump, not a financial summary.
_SUMMARY_PATTERNS = re.compile(
    r"(?:balance\s*sheet|b\.?\s*s\.?"
    r"|p\s*[&.]\s*l|profit|loss|income|expense"
    r"|cash\s*flow"
    r"|notes?\b"
    r"|co\.?,?\s*deprn|company\s*depreciation"
    r"|trading|manufacturing"
    r"|receipt\s*(?:and|&)\s*payment"
    r"|statement|particulars)",
    re.IGNORECASE,
)

# Sheets whose names match these patterns are ALWAYS skipped.
# SKIP takes precedence over SUMMARY, so order matters.
_SKIP_PATTERNS = re.compile(
    r"(?:ledger|g\.?\s*l\.?|general\s*ledger"
    r"|ageing|aging|msme|related\s*party"
    r"|ratio|audit|director|report|annexure"
    r"|stock\s*(?:register|detail|ledger)"
    r"|day\s*book|journal|voucher|bank\s*book"
    r"|gst|tds|tax\s*(?:detail|computation)"
    r"|party|sundry|debtor|creditor"
    r"|memo|comparison|capital\s*wip"
    r"|emi|e\.m\.i"
    r"|def\s*tax|deferred\s*tax"
    r"|depn\s*[-_]?\s*it|depreciation\s*chart"
    r"|sub\s*notes?\b"
    r"|pivot|share\s*hold"
    r"|trial\s*balance|\btb\b)",
    re.IGNORECASE,
)

# Maximum items from a single sheet before we treat it as a ledger dump
_MAX_ITEMS_PER_SHEET = 300

# Minimum absolute amount to be considered a real financial line item.
# Filters out section numbering like (1), (2) which parse_amount reads as -1, -2.
_MIN_AMOUNT = 100.0


def _is_relevant_sheet(name: str) -> bool:
    """Return True when *name* looks like a financial summary sheet."""
    stripped = name.strip()
    if not stripped:
        return False

    # Explicit skip takes precedence
    if _SKIP_PATTERNS.search(stripped):
        logger.info("Sheet '%s' matches skip pattern — excluding", stripped)
        return False

    # Explicit summary match
    if _SUMMARY_PATTERNS.search(stripped):
        logger.info("Sheet '%s' matches summary pattern — including", stripped)
        return True

    # Unknown sheet — EXCLUDE by default to avoid noise from notes/schedules
    logger.info("Sheet '%s' has no pattern match — excluding by default", stripped)
    return False


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


# Scan at most this many columns for numeric values.  Indian financial
# statements place current-year in the first numeric column after the
# description.  Limiting to 10 avoids picking up stale values from
# far-right comparison/breakdown columns.
_MAX_AMOUNT_COLS = 10


def _find_amount_in_row(row_values: list) -> Optional[float]:
    """
    Scan *row_values* for the first significant numeric value (abs >= _MIN_AMOUNT).

    Indian financial statements always place the current year column
    before the previous year column.  By taking the FIRST significant
    number we reliably get the current year, skipping note reference
    numbers (1-30) that appear in earlier columns.

    Only scans the first _MAX_AMOUNT_COLS columns to avoid stale data
    in far-right comparison columns.

    Returns the float value, or None if no significant number is found.
    """
    scan_limit = min(len(row_values), _MAX_AMOUNT_COLS)
    for cell_value in row_values[1:scan_limit]:
        if cell_value is None:
            continue
        candidate: float | None = None
        if isinstance(cell_value, (int, float)) and not isinstance(cell_value, bool):
            candidate = float(cell_value)
        elif isinstance(cell_value, str):
            candidate = parse_amount(cell_value)
        if candidate is not None and abs(candidate) >= _MIN_AMOUNT:
            return candidate
    return None


# ── Sheet priority for deduplication ──────────────────────────────────────────

# Notes / Schedules contain the detailed breakdowns needed for CMA classification.
# Face sheets (P&L, Balance Sheet, Cash Flow) contain summary totals that should
# be superseded by their breakdown counterparts when both are present.
# Higher score = higher priority (preferred when deduplicating).
_FACE_SHEET_PATTERNS = re.compile(
    r"(?:balance\s*sheet|b\.?\s*s\.?"
    r"|p\s*[&.]\s*l|profit\s*(?:and|&)?\s*loss|income\s*statement"
    r"|cash\s*flow"
    r"|trading|manufacturing"
    r"|receipt\s*(?:and|&)\s*payment)",
    re.IGNORECASE,
)

_NOTE_SHEET_PATTERNS = re.compile(
    r"(?:notes?\b|schedule|particular|statement\s*of)",
    re.IGNORECASE,
)


def _sheet_priority(sheet_name: str) -> int:
    """Return a priority score for *sheet_name*.  Higher = preferred for dedup."""
    if _NOTE_SHEET_PATTERNS.search(sheet_name):
        return 3  # Notes / Schedules — PRIMARY (breakdowns)
    if _FACE_SHEET_PATTERNS.search(sheet_name):
        return 1  # Face sheets (P&L, BS) — REFERENCE (totals)
    return 2  # Unknown sheets — middle priority


def _sheet_page_type(sheet_name: str) -> str:
    """Return normalized page_type for a sheet based on its name.

    Notes checked FIRST — sheets like "Notes BS (2)" contain both
    patterns but are Notes breakdowns, not face sheets.
    """
    if _NOTE_SHEET_PATTERNS.search(sheet_name):
        return "notes"
    if _FACE_SHEET_PATTERNS.search(sheet_name):
        return "face"
    return "unknown"


# ── Cross-sheet deduplication ─────────────────────────────────────────────────

# Minimum similarity ratio (0-1) for two descriptions to be considered
# "the same item".  0.85 handles minor wording differences like
# "Revenue from Operations" vs "Revenue From Operations (Net)".
_DEDUP_SIMILARITY_THRESHOLD = 0.85

# Relative tolerance for amounts to be considered "the same".
# 0.001 = 0.1% — handles minor rounding differences.
_DEDUP_AMOUNT_RTOL = 0.001


def _descriptions_match(a: str, b: str) -> bool:
    """Return True if descriptions *a* and *b* refer to the same line item."""
    if not a or not b:
        return False
    # Fast path: exact match after lowercasing
    la, lb = a.lower(), b.lower()
    if la == lb:
        return True
    # Fuzzy match for minor wording differences
    return SequenceMatcher(None, la, lb).ratio() >= _DEDUP_SIMILARITY_THRESHOLD


def _amounts_match(a: float, b: float) -> bool:
    """Return True if amounts are effectively the same."""
    if a == b:
        return True
    if a == 0 and b == 0:
        return True
    # Relative tolerance
    denom = max(abs(a), abs(b))
    if denom == 0:
        return True
    return abs(a - b) / denom <= _DEDUP_AMOUNT_RTOL


def deduplicate_across_sheets(items: list[LineItem]) -> list[LineItem]:
    """Remove duplicate line items that appear identically across multiple sheets.

    When the same financial line item (same description + same amount) appears
    on multiple sheets (e.g. P&L face AND Notes to Accounts), keep only the
    copy from the highest-priority sheet.

    Items with different amounts are NEVER deduplicated — they may represent
    genuinely different line items (e.g. a total on the face vs a sub-item
    in the notes that happens to have a similar name).

    Parameters
    ----------
    items : list[LineItem]
        All items extracted from all sheets (each must have source_sheet set).

    Returns
    -------
    list[LineItem]
        Deduplicated list, preserving original order (within each kept item).
    """
    if not items:
        return items

    # Build groups of items that match on (description, amount).
    # We use a greedy approach: iterate items and assign each to the first
    # existing group that matches, or create a new group.
    groups: list[list[LineItem]] = []

    for item in items:
        matched_group = None
        for group in groups:
            representative = group[0]
            if (_descriptions_match(item.description, representative.description)
                    and _amounts_match(item.amount, representative.amount)):
                matched_group = group
                break
        if matched_group is not None:
            matched_group.append(item)
        else:
            groups.append([item])

    # From each group, pick the item from the highest-priority sheet.
    # On ties, keep the first one encountered (preserves original order).
    kept: list[LineItem] = []
    total_removed = 0

    for group in groups:
        if len(group) == 1:
            kept.append(group[0])
            continue

        # Sort by sheet priority (descending) — first item wins
        group.sort(key=lambda it: _sheet_priority(it.source_sheet), reverse=True)
        winner = group[0]
        kept.append(winner)
        total_removed += len(group) - 1

        if len(group) > 1:
            sheets = [it.source_sheet for it in group]
            logger.info(
                "Dedup: '%s' (amount=%.2f) appeared on %d sheets %s — "
                "keeping from '%s' (priority=%d)",
                winner.description,
                winner.amount,
                len(group),
                sheets,
                winner.source_sheet,
                _sheet_priority(winner.source_sheet),
            )

    if total_removed > 0:
        logger.info(
            "Cross-sheet deduplication removed %d duplicate items "
            "(kept %d of %d total)",
            total_removed,
            len(kept),
            len(items),
        )

    return kept


# ── ExcelExtractor ────────────────────────────────────────────────────────────


class ExcelExtractor:
    """Extracts LineItems from .xlsx and .xls workbooks."""

    async def extract(
        self,
        file_content: bytes,
        file_type: str,
        selected_sheets: list[str] | None = None,
    ) -> list[LineItem]:
        """
        Extract financial line items from an Excel file.

        Parameters
        ----------
        file_content : bytes
            Raw Excel file bytes.
        file_type : str
            "xlsx" or "xls" (case-insensitive).
        selected_sheets : list[str] | None
            If provided, only extract from these sheet names.
            Overrides auto-detection. If None, uses auto-detection.

        Returns
        -------
        list[LineItem]
        """
        try:
            file_type = file_type.lower()
            if file_type == "xlsx":
                return self._extract_xlsx(file_content, selected_sheets)
            elif file_type == "xls":
                return self._extract_xls(file_content, selected_sheets)
            else:
                raise ExtractionError(f"Unsupported file type: {file_type}")
        except ExtractionError:
            raise
        except Exception as e:
            raise ExtractionError(f"Failed to extract Excel file: {e}") from e

    # ── xlsx (openpyxl) ───────────────────────────────────────────────────────

    def _extract_xlsx(self, file_content: bytes, selected_sheets: list[str] | None = None) -> list[LineItem]:
        import openpyxl

        wb = openpyxl.load_workbook(
            io.BytesIO(file_content),
            data_only=True,  # get cell values, not formulas
            read_only=True,
        )

        items: list[LineItem] = []

        for sheet in wb.worksheets:
            sheet_name = sheet.title
            if selected_sheets is not None:
                if sheet_name not in selected_sheets:
                    logger.info("Skipping sheet '%s' (not in user selection)", sheet_name)
                    continue
            elif not _is_relevant_sheet(sheet_name):
                logger.info("Skipping sheet '%s' (filtered out)", sheet_name)
                continue

            sheet_items: list[LineItem] = []
            current_section = ""
            sheet_page_type = _sheet_page_type(sheet_name)
            for row in sheet.iter_rows():
                row_values = [cell.value for cell in row]
                description = self._get_description(row_values)
                if not description:
                    continue  # skip empty rows

                amount = _find_amount_in_row(row_values)

                if amount is None:
                    # No meaningful numeric value → treat as section header
                    if _is_section_header(description):
                        current_section = description.strip().lower()
                    continue

                sheet_items.append(
                    LineItem(
                        description=normalize_line_text(description),
                        amount=amount,
                        section=current_section,
                        raw_text=str(row_values),
                        source_sheet=sheet_name,
                        page_type=sheet_page_type,
                    )
                )

            # Safety net: if a sheet yields too many items, it is likely a
            # ledger / transaction dump — discard it.
            if len(sheet_items) > _MAX_ITEMS_PER_SHEET:
                logger.warning(
                    "Sheet '%s' produced %d items (>%d) — likely a ledger, discarding",
                    sheet_name,
                    len(sheet_items),
                    _MAX_ITEMS_PER_SHEET,
                )
                continue

            logger.info(
                "Sheet '%s' accepted with %d items", sheet_name, len(sheet_items)
            )
            items.extend(sheet_items)

        wb.close()
        return deduplicate_across_sheets(items)

    # ── xls (xlrd) ────────────────────────────────────────────────────────────

    def _extract_xls(self, file_content: bytes, selected_sheets: list[str] | None = None) -> list[LineItem]:
        import xlrd

        wb = xlrd.open_workbook(file_contents=file_content)
        items: list[LineItem] = []

        for sheet in wb.sheets():
            sheet_name = sheet.name
            if selected_sheets is not None:
                if sheet_name not in selected_sheets:
                    logger.info("Skipping sheet '%s' (not in user selection)", sheet_name)
                    continue
            elif not _is_relevant_sheet(sheet_name):
                logger.info("Skipping sheet '%s' (filtered out)", sheet_name)
                continue

            sheet_items: list[LineItem] = []
            current_section = ""
            sheet_page_type = _sheet_page_type(sheet_name)
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

                sheet_items.append(
                    LineItem(
                        description=normalize_line_text(description),
                        amount=amount,
                        section=current_section,
                        raw_text=str(row_values),
                        source_sheet=sheet_name,
                        page_type=sheet_page_type,
                    )
                )

            # Safety net: too many items = likely a ledger
            if len(sheet_items) > _MAX_ITEMS_PER_SHEET:
                logger.warning(
                    "Sheet '%s' produced %d items (>%d) — likely a ledger, discarding",
                    sheet_name,
                    len(sheet_items),
                    _MAX_ITEMS_PER_SHEET,
                )
                continue

            logger.info(
                "Sheet '%s' accepted with %d items", sheet_name, len(sheet_items)
            )
            items.extend(sheet_items)

        return deduplicate_across_sheets(items)

    # ── Shared helpers ────────────────────────────────────────────────────────

    # Short labels that are section/note prefixes, not real descriptions
    _PREFIX_RE = re.compile(
        r"^(?:\(?[a-z0-9]{1,3}\)?\.?|[IVXLC]{1,4}\.?|SL\.?\s*NO\.?|NOTE\s*NO\.?|PARTICULARS)$",
        re.IGNORECASE,
    )

    @staticmethod
    def _get_description(row_values: list) -> str:
        """
        Return the best text label from the first six columns of a row.

        Indian financial statements place descriptions in varying columns
        (A-E).  We scan columns A-F and pick the longest text that is
        NOT a short prefix like "(a)", "I.", "Note No.", etc.
        """
        best = ""
        for idx in range(min(6, len(row_values))):
            val = row_values[idx]
            if not isinstance(val, str):
                continue
            stripped = val.strip()
            if not stripped or len(stripped) < 2:
                continue
            # Skip short prefixes like (a), (1), I., II., SL. NO.
            if ExcelExtractor._PREFIX_RE.match(stripped):
                continue
            # Pick the longest meaningful text
            if len(stripped) > len(best):
                best = stripped
        return best
