"""
extractor_factory.py
====================
Routes a document to the correct extractor based on file type and content.

Hierarchy:
  xlsx / xls  → ExcelExtractor
  pdf (native)→ PdfExtractor
  pdf (scanned→ OcrExtractor

Public API (re-exported for convenience):
  LineItem      — shared dataclass
  parse_amount  — Indian/Western number normalisation
  is_scanned_pdf — detect whether a PDF is image-only
  extract_document — main entry point
"""

from __future__ import annotations

import logging
from io import BytesIO

import pdfplumber

# ── Re-export shared types (tests import LineItem / parse_amount from here) ───
from app.services.extraction._types import ExtractionError, LineItem, parse_amount  # noqa: F401

# ── Extractor classes (imported at module level so patch() can target them) ───
from app.services.extraction.excel_extractor import ExcelExtractor  # noqa: F401
from app.services.extraction.pdf_extractor import PdfExtractor      # noqa: F401
from app.services.extraction.ocr_extractor import OcrExtractor      # noqa: F401
from app.services.extraction.glm_ocr_extractor import GlmOcrExtractor  # noqa: F401
from app.config import get_settings

logger = logging.getLogger(__name__)


# ── Scanned PDF detection ─────────────────────────────────────────────────────


def is_scanned_pdf(file_content: bytes) -> bool:
    """
    Return True when the PDF contains no extractable text on any page.

    A scanned (image-only) PDF will have no text layer — pdfplumber's
    extract_text() returns None or an empty / whitespace-only string.
    """
    try:
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    return False  # at least one page has text → native PDF
        return True  # no page had extractable text → scanned
    except Exception as e:
        raise ExtractionError(f"Failed to read PDF for scanned detection: {e}") from e


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
            settings = get_settings()

            if settings.pdf_extractor == "glm_ocr":
                logger.info("PDF extraction via GLM-OCR (Ollama): %s", file_path)
                items = await GlmOcrExtractor().extract(file_content)
                if not items:
                    logger.warning(
                        "GLM-OCR returned 0 items for %s — falling back to pdfplumber",
                        file_path,
                    )
                    items = await PdfExtractor().extract(file_content)
                return items

            # Legacy path: pdfplumber + OCR fallback
            scanned = is_scanned_pdf(file_content)
            if scanned:
                logger.info("PDF detected as scanned (image-only) → using OcrExtractor: %s", file_path)
                extractor = OcrExtractor()
                items = await extractor.extract(file_content)
            else:
                logger.info("PDF detected as native (has text layer) → using PdfExtractor: %s", file_path)
                items = await PdfExtractor().extract(file_content)
                if not items:
                    logger.warning(
                        "PdfExtractor returned 0 items for %s — falling back to OcrExtractor",
                        file_path,
                    )
                    items = await OcrExtractor().extract(file_content)
                    if items:
                        logger.info(
                            "OcrExtractor fallback succeeded: %d items from %s",
                            len(items), file_path,
                        )
            if not items:
                logger.warning(
                    "PDF extraction returned 0 items after all extractors (scanned=%s, path=%s).",
                    scanned, file_path,
                )
            return items

        raise ExtractionError(
            f"Unsupported file type: '{file_type}'. Must be one of: xlsx, xls, pdf."
        )
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Extraction failed for {file_path}: {e}") from e
