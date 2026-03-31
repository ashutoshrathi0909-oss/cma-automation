"""PDF company name redaction service using PyMuPDF true redaction."""

import re
import pymupdf  # PyMuPDF — imports as 'pymupdf' in newer versions
from io import BytesIO
from dataclasses import dataclass, field


# Indian company name detection regex
INDIAN_COMPANY_PATTERN = re.compile(
    r'([A-Z][A-Za-z\s&\.\-]+?'
    r'(?:Private\s+Limited|Pvt\.?\s*Ltd\.?'
    r'|Corporation\s+Limited|Limited|Ltd\.?|LLP))',
    re.IGNORECASE
)


@dataclass
class RedactionStats:
    pages_processed: int
    total_redactions: int
    per_term: dict[str, int]  # {term: count}
    detected_names: list[str] = field(default_factory=list)


def detect_company_names(pdf_bytes: bytes) -> list[str]:
    """Auto-detect company names from first page of PDF.

    Strategy 1: Large font spans (size >= 14) in top 200px of page 1
    Strategy 2: Indian company name regex on header text
    Returns deduplicated list of candidates for user confirmation.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    candidates = []

    # Strategy 1: Large-font text in header region
    text_dict = page.get_text("dict")
    for block in text_dict["blocks"]:
        if block["type"] == 0:  # text block
            for line in block["lines"]:
                for span in line["spans"]:
                    if span["size"] >= 14 and span["origin"][1] < 200:
                        text = span["text"].strip()
                        if text and len(text) > 3:
                            candidates.append(text)

    # Strategy 2: Regex on header clip
    header_clip = pymupdf.Rect(0, 0, page.rect.width, 200)
    header_text = page.get_text(clip=header_clip)
    regex_matches = INDIAN_COMPANY_PATTERN.findall(header_text)
    candidates.extend([m.strip() for m in regex_matches])

    doc.close()

    # Deduplicate preserving order
    seen = set()
    unique = []
    for c in candidates:
        if c.lower() not in seen and len(c) > 3:
            seen.add(c.lower())
            unique.append(c)
    return unique


def preview_redaction(pdf_bytes: bytes, terms: list[str]) -> dict[str, int]:
    """Count instances of each term across all pages. No modifications.

    Returns: {term: instance_count}
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    counts = {term: 0 for term in terms}

    for page in doc:
        for term in terms:
            instances = page.search_for(term)
            counts[term] += len(instances)

    doc.close()
    return counts


def apply_redaction(pdf_bytes: bytes, terms: list[str]) -> tuple[bytes, RedactionStats]:
    """Apply true redaction to PDF. Permanently removes text data.

    SECURITY:
    - White fill (1,1,1) — no OCR noise for downstream processing
    - Preserve table borders (PDF_REDACT_LINE_ART_NONE)
    - Handle scanned PDFs (PDF_REDACT_IMAGE_PIXELS blanks image pixels)
    - Full save with garbage=4 (no incremental — forensically sound)
    - Metadata scrubbed (author, title, dates, XMP)
    - Post-redaction verification: assert zero matches remain

    Returns: (redacted_pdf_bytes, stats)
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    total = 0
    per_term = {term: 0 for term in terms}

    for page in doc:
        for term in terms:
            instances = page.search_for(term)
            for inst in instances:
                page.add_redact_annot(inst, fill=(1, 1, 1))  # white fill
                per_term[term] += 1
                total += 1
        # Apply ALL redactions for this page at once (performance)
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_PIXELS,    # blanks image pixels too
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE, # preserves table borders
        )

    # Scrub metadata
    doc.set_metadata({k: "" for k in doc.metadata})
    doc.del_xml_metadata()

    # Full save — forensically sound (removes orphaned objects)
    output = BytesIO()
    doc.save(output, garbage=4, deflate=True)
    pages_processed = len(doc)
    doc.close()

    redacted_bytes = output.getvalue()

    # Post-redaction verification
    verify_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
    for page in verify_doc:
        for term in terms:
            assert len(page.search_for(term)) == 0, f"Redaction failed: '{term}' still found"
    verify_doc.close()

    return redacted_bytes, RedactionStats(
        pages_processed=pages_processed,
        total_redactions=total,
        per_term=per_term,
        detected_names=[],  # filled by caller if auto-detect was used
    )
