"""
extractor_factory.py
====================
Routes a document to the correct extractor based on file type and content.

Hierarchy:
  xlsx / xls  → ExcelExtractor
  pdf         → OcrExtractor (Gemini Flash vision via OpenRouter — all PDFs)

Public API (re-exported for convenience):
  LineItem      — shared dataclass
  parse_amount  — Indian/Western number normalisation
  extract_document — main entry point
"""

from __future__ import annotations

import logging

# ── Re-export shared types (tests import LineItem / parse_amount from here) ───
from app.services.extraction._types import ExtractionError, LineItem, parse_amount  # noqa: F401

# ── Extractor classes (imported at module level so patch() can target them) ───
from app.services.extraction.excel_extractor import ExcelExtractor  # noqa: F401
from app.services.extraction.ocr_extractor import OcrExtractor      # noqa: F401

logger = logging.getLogger(__name__)


# ── Factory entry point ───────────────────────────────────────────────────────


async def extract_document(
    file_content: bytes,
    file_type: str,
    file_path: str,
    selected_sheets: list[str] | None = None,
) -> list[LineItem]:
    """
    Route *file_content* to the appropriate extractor and return line items.

    Parameters
    ----------
    file_content : bytes
        Raw file bytes (already downloaded from Supabase Storage).
    file_type : str
        One of "xlsx", "xls", "pdf".
    file_path : str
        Supabase Storage path (used only for logging / error messages).
    selected_sheets : list[str] | None
        If provided, only extract from these sheet names (Excel only).
        If None, uses auto-detection.

    Returns
    -------
    list[LineItem]
        Extracted financial line items, ready for the classification pipeline.

    Raises
    ------
    ExtractionError
        If the file cannot be extracted or *file_type* is not supported.
    """
    logger.info("Extracting document: %s (type=%s, selected_sheets=%s)", file_path, file_type, selected_sheets)
    try:
        file_type = file_type.lower()

        if file_type in ("xlsx", "xls"):
            extractor = ExcelExtractor()
            return await extractor.extract(file_content, file_type, selected_sheets=selected_sheets)

        if file_type == "pdf":
            logger.info("PDF extraction via vision AI (OpenRouter): %s", file_path)
            extractor = OcrExtractor()
            items = await extractor.extract(file_content)
            if not items:
                logger.warning(
                    "Vision extraction returned 0 items for %s. "
                    "The document may not contain recognizable financial data.",
                    file_path,
                )
            return items

        raise ExtractionError(
            f"Unsupported file type: '{file_type}'. Must be one of: xlsx, xls, pdf."
        )
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Extraction failed for {file_path}: {e}") from e
