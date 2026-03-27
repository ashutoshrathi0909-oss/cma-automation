"""Tests for pdf/page_manager.py — PDF page removal utilities.

Covers:
  - parse_page_ranges: empty, simple range, comma list, mixed, invalid, out-of-bounds,
    reversed range, single-page range
  - pages_to_keep: normal removal, empty string (keep all)
  - remove_pages: multi-page removal, keep-all, keep-single, empty keep_pages error
  - get_page_count: correct count for test PDF
"""

import pytest
import pikepdf
from io import BytesIO

from app.services.pdf.page_manager import (
    parse_page_ranges,
    pages_to_keep,
    remove_pages,
    get_page_count,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def make_test_pdf(num_pages: int) -> bytes:
    """Create a minimal valid PDF with the given number of blank pages."""
    pdf = pikepdf.Pdf.new()
    for _ in range(num_pages):
        pdf.add_blank_page()
    buf = BytesIO()
    pdf.save(buf)
    return buf.getvalue()


# ── parse_page_ranges ──────────────────────────────────────────────────────────


class TestParsePageRanges:
    def test_empty_string_returns_empty_list(self):
        assert parse_page_ranges("", 10) == []

    def test_whitespace_only_returns_empty_list(self):
        assert parse_page_ranges("   ", 10) == []

    def test_simple_range_returns_correct_pages(self):
        assert parse_page_ranges("1-2", 10) == [1, 2]

    def test_comma_separated_pages(self):
        assert parse_page_ranges("1, 3, 5", 10) == [1, 3, 5]

    def test_mixed_ranges_and_individual_pages(self):
        result = parse_page_ranges("1-3, 7, 10-12", 15)
        assert result == [1, 2, 3, 7, 10, 11, 12]

    def test_invalid_token_is_ignored_valid_range_kept(self):
        # "abc" is invalid; "1-2" should still be returned
        result = parse_page_ranges("abc, 1-2", 10)
        assert result == [1, 2]

    def test_out_of_range_pages_excluded(self):
        # Page 0 and page 100 are both out of [1, 10]
        result = parse_page_ranges("0, 100", 10)
        assert result == []

    def test_reversed_range_is_normalised(self):
        # "5-3" should be treated as "3-5"
        result = parse_page_ranges("5-3", 10)
        assert result == [3, 4, 5]

    def test_single_page_range(self):
        assert parse_page_ranges("1-1", 10) == [1]

    def test_range_clipped_to_total_pages(self):
        # Range extends beyond total_pages; only valid pages returned
        result = parse_page_ranges("8-12", 10)
        assert result == [8, 9, 10]

    def test_duplicates_are_deduplicated(self):
        # Page 2 appears via range and explicit entry
        result = parse_page_ranges("1-3, 2, 3", 10)
        assert result == [1, 2, 3]


# ── pages_to_keep ──────────────────────────────────────────────────────────────


class TestPagesToKeep:
    def test_remove_first_two_of_five(self):
        result = pages_to_keep("1-2", 5)
        assert result == [3, 4, 5]

    def test_empty_string_keeps_all_pages(self):
        result = pages_to_keep("", 5)
        assert result == [1, 2, 3, 4, 5]

    def test_remove_single_middle_page(self):
        result = pages_to_keep("3", 5)
        assert result == [1, 2, 4, 5]

    def test_remove_all_pages_returns_empty(self):
        result = pages_to_keep("1-5", 5)
        assert result == []


# ── remove_pages ───────────────────────────────────────────────────────────────


class TestRemovePages:
    def test_remove_first_two_pages_of_five(self):
        pdf_bytes = make_test_pdf(5)
        keep = pages_to_keep("1-2", 5)   # [3, 4, 5]
        result = remove_pages(pdf_bytes, keep)
        assert get_page_count(result) == 3

    def test_keep_all_pages_output_matches_input_count(self):
        pdf_bytes = make_test_pdf(4)
        keep = list(range(1, 5))          # [1, 2, 3, 4]
        result = remove_pages(pdf_bytes, keep)
        assert get_page_count(result) == 4

    def test_keep_single_page(self):
        pdf_bytes = make_test_pdf(6)
        result = remove_pages(pdf_bytes, [3])
        assert get_page_count(result) == 1

    def test_empty_keep_pages_raises_value_error(self):
        pdf_bytes = make_test_pdf(3)
        with pytest.raises(ValueError, match="keep_pages must not be empty"):
            remove_pages(pdf_bytes, [])

    def test_output_is_valid_pdf_bytes(self):
        pdf_bytes = make_test_pdf(3)
        result = remove_pages(pdf_bytes, [1, 3])
        # Must be parseable by pikepdf
        with pikepdf.Pdf.open(BytesIO(result)) as pdf:
            assert len(pdf.pages) == 2

    def test_out_of_range_keep_pages_ignored(self):
        # keep_pages contains page 99 which doesn't exist; only page 1 is valid
        pdf_bytes = make_test_pdf(3)
        result = remove_pages(pdf_bytes, [1, 99])
        assert get_page_count(result) == 1


# ── get_page_count ─────────────────────────────────────────────────────────────


class TestGetPageCount:
    def test_single_page_pdf(self):
        pdf_bytes = make_test_pdf(1)
        assert get_page_count(pdf_bytes) == 1

    def test_multi_page_pdf(self):
        pdf_bytes = make_test_pdf(7)
        assert get_page_count(pdf_bytes) == 7

    def test_page_count_after_removal(self):
        pdf_bytes = make_test_pdf(5)
        trimmed = remove_pages(pdf_bytes, [2, 4])
        assert get_page_count(trimmed) == 2
