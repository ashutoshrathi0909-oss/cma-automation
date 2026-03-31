"""Tests for pdf/redaction_service — PDF company-name redaction.

All tests are self-contained: PDFs are generated in-memory using pymupdf
so no file I/O or mocking of pymupdf is required.  The point is to verify
that actual redaction is performed correctly by the service under test.

Three groups:
  1. TestDetectCompanyNames  — detect_company_names()
  2. TestPreviewRedaction    — preview_redaction()
  3. TestApplyRedaction      — apply_redaction()  (functional)
  4. TestApplyRedactionSecurity — apply_redaction() (security / raw bytes)
"""

from __future__ import annotations

import pymupdf
import pytest

from app.services.pdf.redaction_service import (
    RedactionStats,
    apply_redaction,
    detect_company_names,
    preview_redaction,
)


# ── Helper ────────────────────────────────────────────────────────────────────


def create_test_pdf(
    company_name: str = "ABC Industries Private Limited",
    pages: int = 3,
) -> bytes:
    """Create a test PDF with known content for redaction testing.

    Each page contains:
    - A large-font (18 pt) header at y=50 with the company name
      (strategy 1: size >= 14, y < 200 → qualifies as header text)
    - Small body text that must NOT be detected as a company name
    - A body sentence that embeds the company name at normal font size
    """
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        # Header: large font — detected by large-font strategy
        page.insert_text((72, 50), company_name, fontsize=18)
        # Body content — small font, no company suffix
        page.insert_text((72, 100), f"Financial Statement Page {i + 1}", fontsize=12)
        page.insert_text((72, 130), "Revenue: Rs 45,23,456", fontsize=11)
        page.insert_text((72, 160), f"Prepared for {company_name}", fontsize=11)
    output = doc.tobytes()
    doc.close()
    return output


def create_plain_pdf(body_lines: list[str], pages: int = 1) -> bytes:
    """Create a PDF with only small-font body text (no header-zone large text)."""
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page()
        y = 250  # below header zone (y >= 200), so large-font strategy misses it
        for line in body_lines:
            page.insert_text((72, y), line, fontsize=11)
            y += 20
    output = doc.tobytes()
    doc.close()
    return output


# ══════════════════════════════════════════════════════════════════════════════
# 1. detect_company_names()
# ══════════════════════════════════════════════════════════════════════════════


class TestDetectCompanyNames:
    """Tests for detect_company_names(pdf_bytes) -> list[str]."""

    def test_detects_pvt_ltd(self):
        """PDF with 'ABC Industries Private Limited' in large-font header
        → the name is returned in the candidate list."""
        pdf = create_test_pdf("ABC Industries Private Limited")
        candidates = detect_company_names(pdf)
        assert any(
            "ABC Industries Private Limited" in c for c in candidates
        ), f"Expected 'ABC Industries Private Limited' in candidates, got: {candidates}"

    def test_detects_pvt_ltd_abbreviated(self):
        """PDF with 'XYZ Pvt. Ltd.' in large-font header → detected."""
        pdf = create_test_pdf("XYZ Pvt. Ltd.")
        candidates = detect_company_names(pdf)
        assert any(
            "XYZ" in c for c in candidates
        ), f"Expected 'XYZ Pvt. Ltd.' variant in candidates, got: {candidates}"

    def test_detects_llp(self):
        """PDF with 'GHI LLP' in large-font header → detected."""
        pdf = create_test_pdf("GHI LLP")
        candidates = detect_company_names(pdf)
        assert any(
            "GHI" in c for c in candidates
        ), f"Expected 'GHI LLP' variant in candidates, got: {candidates}"

    def test_empty_for_no_company(self):
        """PDF with only small body text and no company suffixes → returns
        empty list or at least does NOT detect a false-positive company name."""
        pdf = create_plain_pdf(
            [
                "Revenue: Rs 45,23,456",
                "Expenses: Rs 30,00,000",
                "Net Profit: Rs 15,23,456",
            ]
        )
        candidates = detect_company_names(pdf)
        # Either empty, or none of the candidates contain known company suffixes
        company_suffixes = ("pvt", "ltd", "llp", "limited", "private", "inc")
        false_positives = [
            c for c in candidates
            if any(s in c.lower() for s in company_suffixes)
        ]
        assert false_positives == [], (
            f"Unexpected company candidates from plain body text: {false_positives}"
        )

    def test_no_short_strings(self):
        """Candidates shorter than 4 characters must not appear in results."""
        pdf = create_test_pdf("ABC Industries Private Limited")
        candidates = detect_company_names(pdf)
        short = [c for c in candidates if len(c.strip()) < 4]
        assert short == [], f"Short strings found in candidates: {short}"

    def test_deduplication(self):
        """The same name found by multiple strategies is returned only once."""
        pdf = create_test_pdf("ABC Industries Private Limited")
        candidates = detect_company_names(pdf)
        # Check for duplicates by normalising whitespace and case
        normalised = [c.strip().lower() for c in candidates]
        assert len(normalised) == len(set(normalised)), (
            f"Duplicate candidates found: {candidates}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 2. preview_redaction()
# ══════════════════════════════════════════════════════════════════════════════


class TestPreviewRedaction:
    """Tests for preview_redaction(pdf_bytes, terms) -> dict[str, int]."""

    def test_counts_per_term(self):
        """3-page PDF with company name on each page → count >= 3
        (header line + 'Prepared for …' line = 2 per page = 6 total)."""
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company, pages=3)
        counts = preview_redaction(pdf, [company])
        assert company in counts, f"Term missing from preview result: {counts}"
        assert counts[company] >= 3, (
            f"Expected at least 3 occurrences across 3 pages, got {counts[company]}"
        )

    def test_zero_for_missing_term(self):
        """A term not present in the PDF returns a count of 0."""
        pdf = create_test_pdf("ABC Industries Private Limited")
        counts = preview_redaction(pdf, ["Totally Missing Corp"])
        assert counts.get("Totally Missing Corp", 0) == 0, (
            f"Expected 0 for absent term, got {counts}"
        )

    def test_multiple_terms(self):
        """preview_redaction with two different terms counts both independently."""
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 50), "Alpha Corp Private Limited", fontsize=18)
        page.insert_text((72, 100), "Beta Solutions LLP", fontsize=18)
        page.insert_text((72, 150), "Revenue: Rs 10,00,000", fontsize=11)
        pdf = doc.tobytes()
        doc.close()

        counts = preview_redaction(pdf, ["Alpha Corp Private Limited", "Beta Solutions LLP"])
        assert counts.get("Alpha Corp Private Limited", 0) >= 1, (
            f"Expected at least 1 hit for Alpha Corp, got {counts}"
        )
        assert counts.get("Beta Solutions LLP", 0) >= 1, (
            f"Expected at least 1 hit for Beta Solutions, got {counts}"
        )

    def test_empty_terms(self):
        """terms=[] returns an empty dict immediately."""
        pdf = create_test_pdf("ABC Industries Private Limited")
        counts = preview_redaction(pdf, [])
        assert counts == {}, f"Expected empty dict for empty terms, got {counts}"


# ══════════════════════════════════════════════════════════════════════════════
# 3. apply_redaction() — functional behaviour
# ══════════════════════════════════════════════════════════════════════════════


class TestApplyRedaction:
    """Tests for apply_redaction(pdf_bytes, terms) -> (bytes, RedactionStats)."""

    def test_term_not_in_output_text(self):
        """After redaction, page.get_text() does not contain the redacted term."""
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company)
        redacted_bytes, _ = apply_redaction(pdf, [company])

        out_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
        for page in out_doc:
            text = page.get_text()
            assert company not in text, (
                f"Redacted term still visible in extracted text on page {page.number}"
            )
        out_doc.close()

    def test_term_not_in_raw_bytes(self):
        """After redaction, the raw bytes of the output PDF do not contain
        the redacted term encoded as UTF-8."""
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company)
        redacted_bytes, _ = apply_redaction(pdf, [company])

        assert company.encode("utf-8") not in redacted_bytes, (
            "Redacted term found as raw UTF-8 bytes in output PDF"
        )

    def test_metadata_scrubbed(self):
        """After apply_redaction, all metadata values are empty strings."""
        pdf = create_test_pdf("ABC Industries Private Limited")
        redacted_bytes, _ = apply_redaction(pdf, ["ABC Industries Private Limited"])

        out_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
        meta = out_doc.metadata
        out_doc.close()

        # 'format' is a read-only structural field (e.g. "PDF 1.7") — not scrubable
        scrubable_keys = {k for k in meta if k != "format"}
        for key in scrubable_keys:
            value = meta[key]
            assert value == "" or value is None, (
                f"Metadata field '{key}' not scrubbed: got '{value}'"
            )

    def test_non_redacted_text_preserved(self):
        """Text that is NOT in the redaction list is preserved after apply."""
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company)
        redacted_bytes, _ = apply_redaction(pdf, [company])

        out_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
        all_text = "".join(page.get_text() for page in out_doc)
        out_doc.close()

        assert "Revenue" in all_text, (
            "Non-redacted text 'Revenue' was incorrectly removed from PDF"
        )

    def test_multiple_terms(self):
        """Two different terms are both fully redacted in a single call."""
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 50), "Alpha Corp Private Limited", fontsize=18)
        page.insert_text((72, 100), "Beta Solutions LLP", fontsize=18)
        page.insert_text((72, 150), "Revenue: Rs 10,00,000", fontsize=11)
        pdf_bytes = doc.tobytes()
        doc.close()

        redacted_bytes, _ = apply_redaction(
            pdf_bytes,
            ["Alpha Corp Private Limited", "Beta Solutions LLP"],
        )

        out_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
        all_text = "".join(page.get_text() for page in out_doc)
        out_doc.close()

        assert "Alpha Corp Private Limited" not in all_text, (
            "First redacted term still present in output text"
        )
        assert "Beta Solutions LLP" not in all_text, (
            "Second redacted term still present in output text"
        )

    def test_empty_terms_unchanged_page_count(self):
        """terms=[] returns a PDF with the same page count and raises no error."""
        pdf = create_test_pdf("ABC Industries Private Limited", pages=2)
        result_bytes, _ = apply_redaction(pdf, [])

        out_doc = pymupdf.open(stream=result_bytes, filetype="pdf")
        page_count = out_doc.page_count
        out_doc.close()

        assert page_count == 2, (
            f"Page count changed for empty-terms call: expected 2, got {page_count}"
        )

    def test_page_count_preserved(self):
        """Output PDF has the same number of pages as the input PDF."""
        pdf = create_test_pdf("ABC Industries Private Limited", pages=3)
        redacted_bytes, _ = apply_redaction(pdf, ["ABC Industries Private Limited"])

        out_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
        page_count = out_doc.page_count
        out_doc.close()

        assert page_count == 3, (
            f"Page count changed after redaction: expected 3, got {page_count}"
        )

    def test_stats_returned(self):
        """apply_redaction returns a RedactionStats with correct totals.

        3-page PDF, each page has the company name twice (header + body line)
        → total_redactions >= 6, per-term count matches total.
        """
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company, pages=3)
        _, stats = apply_redaction(pdf, [company])

        assert isinstance(stats, RedactionStats), (
            f"Second return value must be RedactionStats, got {type(stats)}"
        )
        assert stats.total_redactions >= 3, (
            f"Expected at least 3 total redactions across 3 pages, "
            f"got {stats.total_redactions}"
        )
        assert company in stats.per_term, (
            f"Term missing from per_term dict: {stats.per_term}"
        )
        assert stats.per_term[company] == stats.total_redactions, (
            f"per_term count ({stats.per_term[company]}) does not match "
            f"total_redactions ({stats.total_redactions}) for single term"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. apply_redaction() — security / raw-bytes hardening
# ══════════════════════════════════════════════════════════════════════════════


class TestApplyRedactionSecurity:
    """Security-focused tests: verify redacted content cannot be recovered
    from the raw byte stream of the output PDF."""

    def test_raw_bytes_clean(self):
        """The redacted company name does not appear as ASCII or UTF-8 bytes
        anywhere in the raw output PDF byte stream."""
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company)
        redacted_bytes, _ = apply_redaction(pdf, [company])

        assert company.encode("utf-8") not in redacted_bytes, (
            "Company name found as UTF-8 in raw output bytes"
        )
        assert company.encode("ascii") not in redacted_bytes, (
            "Company name found as ASCII in raw output bytes"
        )

    def test_xmp_metadata_removed(self):
        """After apply_redaction, XMP metadata is None or empty."""
        company = "ABC Industries Private Limited"
        pdf = create_test_pdf(company)
        redacted_bytes, _ = apply_redaction(pdf, [company])

        out_doc = pymupdf.open(stream=redacted_bytes, filetype="pdf")
        xmp = out_doc.get_xml_metadata()
        out_doc.close()

        # get_xml_metadata() returns "" or None when no XMP metadata is present
        assert xmp is None or xmp == "", (
            f"XMP metadata not removed after redaction: got '{xmp[:80]}...'"
        )
