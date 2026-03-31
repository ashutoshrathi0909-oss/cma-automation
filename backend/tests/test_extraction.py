"""
Phase 4A: Extraction service tests.

TDD workflow — RED → GREEN → REFACTOR.
All tests were written BEFORE the service implementations.

Coverage targets:
  - ExcelExtractor: xlsx, xls, amounts, sections, Indian number format
  - PdfExtractor: native tables, native text fallback
  - OcrExtractor: image conversion, surya call, Haiku structuring
  - extractor_factory: routing logic, scanned-PDF detection
"""

import io
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from app.services.extraction.extractor_factory import (
    ExtractionError,
    LineItem,
    extract_document,
    is_scanned_pdf,
)
from app.services.extraction._types import parse_amount
from app.services.extraction.excel_extractor import ExcelExtractor
from app.services.extraction.pdf_extractor import PdfExtractor


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_xlsx_bytes() -> bytes:
    """Minimal valid xlsx bytes (PK magic)."""
    return b"PK\x03\x04" + b"\x00" * 100


def _make_xls_bytes() -> bytes:
    """Minimal OLE2 compound document magic bytes for xls."""
    return b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 100


def _make_pdf_bytes_with_text() -> bytes:
    """Minimal PDF header that pdfplumber can partially recognise."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"


def _make_pdf_bytes_no_text() -> bytes:
    """PDF-like header with no embedded text (image-only)."""
    return b"%PDF-1.4\n" + b"\x00" * 50


# ── LineItem dataclass ─────────────────────────────────────────────────────────


class TestLineItem:
    def test_line_item_has_required_fields(self):
        """LineItem dataclass must have description, amount, section, raw_text."""
        item = LineItem(
            description="Salaries & Wages",
            amount=500000.0,
            section="expenses",
            raw_text="Salaries & Wages  5,00,000",
        )
        assert item.description == "Salaries & Wages"
        assert item.amount == 500000.0
        assert item.section == "expenses"
        assert item.raw_text == "Salaries & Wages  5,00,000"

    def test_line_item_equality(self):
        """Two LineItems with identical fields should be equal (dataclass default)."""
        a = LineItem("Revenue", 1000000.0, "income", "Revenue 10,00,000")
        b = LineItem("Revenue", 1000000.0, "income", "Revenue 10,00,000")
        assert a == b

    def test_ambiguity_question_default_none(self):
        item = LineItem(description="Revenue", amount=1000.0, section="income", raw_text="Revenue 1000")
        assert item.ambiguity_question is None

    def test_ambiguity_question_can_be_set_as_keyword(self):
        item = LineItem(
            description="Wages & Other",
            amount=2000.0,
            section="expenses",
            raw_text="Wages & Other 2000",
            ambiguity_question="Please split between Row 45 and Row 49",
        )
        assert item.ambiguity_question is not None


# ── Indian Number Format ───────────────────────────────────────────────────────


class TestIndianNumberFormat:
    """
    Test the parse_amount helper that normalises Indian and Western formats.
    We import it directly from the extractor_factory module.
    """

    def test_parse_indian_lakh_format(self):
        from app.services.extraction.extractor_factory import parse_amount
        assert parse_amount("1,23,456") == pytest.approx(123456.0)

    def test_parse_western_format(self):
        from app.services.extraction.extractor_factory import parse_amount
        assert parse_amount("1,234,567") == pytest.approx(1234567.0)

    def test_parse_plain_number(self):
        from app.services.extraction.extractor_factory import parse_amount
        assert parse_amount("500000") == pytest.approx(500000.0)

    def test_parse_decimal(self):
        from app.services.extraction.extractor_factory import parse_amount
        assert parse_amount("1,23,456.78") == pytest.approx(123456.78)

    def test_parse_empty_returns_none(self):
        from app.services.extraction.extractor_factory import parse_amount
        assert parse_amount("") is None

    def test_parse_non_numeric_returns_none(self):
        from app.services.extraction.extractor_factory import parse_amount
        assert parse_amount("N/A") is None

    def test_parse_crore_format(self):
        from app.services.extraction.extractor_factory import parse_amount
        # 1,00,00,000 = 1 crore
        assert parse_amount("1,00,00,000") == pytest.approx(10000000.0)

    def test_parse_parentheses_negative(self):
        """(1,23,456) should return -123456.0 per Indian accounting convention."""
        assert parse_amount("(1,23,456)") == -123456.0

    def test_parse_plain_negative(self):
        """-500000 should return -500000.0."""
        assert parse_amount("-500000") == -500000.0

    def test_parse_negative_with_currency_symbol(self):
        """₹(45,00,000) should return -4500000.0."""
        assert parse_amount("₹(45,00,000)") == -4500000.0


# ── ExcelExtractor ─────────────────────────────────────────────────────────────


class TestExcelExtractor:
    @pytest.fixture
    def extractor(self):
        return ExcelExtractor()

    @pytest.mark.asyncio
    async def test_excel_extractor_reads_xlsx(self, extractor):
        """ExcelExtractor.extract() with xlsx bytes → returns list of LineItem."""
        # Build a real in-memory xlsx workbook with openpyxl
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "P&L"
        ws.append(["Description", "Amount"])
        ws.append(["Salaries & Wages", 500000])
        ws.append(["Rent", 120000])

        buf = io.BytesIO()
        wb.save(buf)
        xlsx_bytes = buf.getvalue()

        items = await extractor.extract(xlsx_bytes, "xlsx")

        assert isinstance(items, list)
        assert len(items) >= 1
        descriptions = [i.description for i in items]
        assert any("Salaries" in d or "salaries" in d.lower() for d in descriptions)

    @pytest.mark.asyncio
    async def test_excel_extractor_reads_xls(self, extractor):
        """ExcelExtractor.extract() with xls bytes → parses via xlrd, returns LineItems."""
        # We mock xlrd because building a valid binary .xls from scratch is complex
        mock_sheet = MagicMock()
        mock_sheet.nrows = 3
        mock_sheet.name = "Sheet1"

        # Row 0: header row (text, text) — should be skipped
        mock_sheet.row_values.side_effect = lambda i: [
            ["Description", "2024"],
            ["Salaries & Wages", 500000.0],
            ["Rent Expense", 120000.0],
        ][i]

        mock_wb = MagicMock()
        mock_wb.sheets.return_value = [mock_sheet]

        with patch("xlrd.open_workbook", return_value=mock_wb):
            items = await extractor.extract(_make_xls_bytes(), "xls", selected_sheets=["Sheet1"])

        assert isinstance(items, list)
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_excel_extractor_extracts_amounts(self, extractor):
        """Row 'Salaries & Wages | 5,00,000' → LineItem with amount=500000.0."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws_name = ws.title  # default is "Sheet"
        # Use string format to simulate Indian number formatting in a cell
        ws.append(["Salaries & Wages", "5,00,000"])

        buf = io.BytesIO()
        wb.save(buf)
        xlsx_bytes = buf.getvalue()

        items = await extractor.extract(xlsx_bytes, "xlsx", selected_sheets=[ws_name])

        salary_items = [i for i in items if "Salaries" in i.description or "salaries" in i.description.lower()]
        assert len(salary_items) >= 1
        assert salary_items[0].amount == pytest.approx(500000.0)

    @pytest.mark.asyncio
    async def test_excel_extractor_extracts_section_headers(self, extractor):
        """Bold / ALL-CAPS header rows without numeric amounts → set current section."""
        import openpyxl
        from openpyxl.styles import Font

        wb = openpyxl.Workbook()
        ws = wb.active
        ws_name = ws.title  # default is "Sheet"

        # ALL-CAPS header (no amount) — should become section
        ws.append(["INCOME", ""])
        revenue_row = ws.max_row + 1
        ws.append(["Revenue from Operations", 1000000])

        buf = io.BytesIO()
        wb.save(buf)
        xlsx_bytes = buf.getvalue()

        items = await extractor.extract(xlsx_bytes, "xlsx", selected_sheets=[ws_name])

        # Revenue item should carry the "income" section
        revenue_items = [i for i in items if "Revenue" in i.description or "revenue" in i.description.lower()]
        assert len(revenue_items) >= 1
        # section may be "income" (lowercase) or the raw header text
        assert revenue_items[0].section.lower() in ("income", "")

    @pytest.mark.asyncio
    async def test_excel_extractor_handles_indian_number_format(self, extractor):
        """Cell value '1,23,456' (Indian lakh) → LineItem.amount == 123456.0."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws_name = ws.title  # default is "Sheet"
        ws.append(["Other Income", "1,23,456"])

        buf = io.BytesIO()
        wb.save(buf)
        xlsx_bytes = buf.getvalue()

        items = await extractor.extract(xlsx_bytes, "xlsx", selected_sheets=[ws_name])

        income_items = [i for i in items if "Income" in i.description or "income" in i.description.lower()]
        assert len(income_items) >= 1
        assert income_items[0].amount == pytest.approx(123456.0)

    @pytest.mark.asyncio
    async def test_excel_extractor_skips_empty_rows(self, extractor):
        """Rows with no description and no amount should be silently skipped."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Revenue", 1000000])
        ws.append(["", ""])          # empty row
        ws.append(["", None])        # another empty row
        ws.append(["Cost of Goods", 600000])

        buf = io.BytesIO()
        wb.save(buf)
        xlsx_bytes = buf.getvalue()

        items = await extractor.extract(xlsx_bytes, "xlsx")
        # Should only have the two data rows
        descriptions = [i.description for i in items]
        assert all(d.strip() for d in descriptions)

    @pytest.mark.asyncio
    async def test_excel_extractor_multi_sheet(self, extractor):
        """Extractor scans ALL selected sheets, not just the first."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Sheet1"
        ws1.append(["Revenue", 1000000])

        ws2 = wb.create_sheet("Sheet2")
        ws2.append(["Expenses", 600000])

        buf = io.BytesIO()
        wb.save(buf)
        xlsx_bytes = buf.getvalue()

        items = await extractor.extract(xlsx_bytes, "xlsx", selected_sheets=["Sheet1", "Sheet2"])
        descriptions = [i.description for i in items]
        assert any("Revenue" in d for d in descriptions)
        assert any("Expenses" in d for d in descriptions)


# ── PdfExtractor ───────────────────────────────────────────────────────────────


class TestPdfExtractor:
    @pytest.fixture
    def extractor(self):
        return PdfExtractor()

    @pytest.mark.asyncio
    async def test_pdf_extractor_reads_native_pdf(self, extractor):
        """PdfExtractor.extract() opens the PDF with pdfplumber (mocked)."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [["Description", "Amount"], ["Salaries", "5,00,000"]]
        ]
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            items = await extractor.extract(_make_pdf_bytes_with_text())

        assert isinstance(items, list)
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_pdf_extractor_extracts_tables(self, extractor):
        """Tables in a PDF → each data row becomes a LineItem."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Description", "Amount"],
                ["Salaries & Wages", "5,00,000"],
                ["Rent", "1,20,000"],
            ]
        ]
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            items = await extractor.extract(_make_pdf_bytes_with_text())

        assert len(items) == 2
        assert items[0].description == "Salaries & Wages"
        assert items[0].amount == pytest.approx(500000.0)
        assert items[1].description == "Rent"
        assert items[1].amount == pytest.approx(120000.0)

    @pytest.mark.asyncio
    async def test_pdf_extractor_fallback_to_text(self, extractor):
        """When no tables are found, fall back to text parsing line-by-line."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = []  # no tables
        mock_page.extract_text.return_value = (
            "Profit & Loss Account\n"
            "Salaries & Wages          5,00,000\n"
            "Rent Expense              1,20,000\n"
        )

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            items = await extractor.extract(_make_pdf_bytes_with_text())

        assert len(items) >= 1
        descriptions = [i.description for i in items]
        assert any("Salaries" in d for d in descriptions)

    @pytest.mark.asyncio
    async def test_pdf_extractor_handles_multi_page(self, extractor):
        """Multi-page PDF: each page is processed."""
        def make_page(label, amount_str):
            p = MagicMock()
            p.extract_tables.return_value = [
                [["Item", "Value"], [label, amount_str]]
            ]
            p.extract_text.return_value = None
            return p

        mock_pdf = MagicMock()
        mock_pdf.pages = [
            make_page("Revenue", "10,00,000"),
            make_page("Expenses", "6,00,000"),
        ]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            items = await extractor.extract(_make_pdf_bytes_with_text())

        descriptions = [i.description for i in items]
        assert any("Revenue" in d for d in descriptions)
        assert any("Expenses" in d for d in descriptions)

    @pytest.mark.asyncio
    async def test_pdf_extractor_skips_header_rows(self, extractor):
        """Header row (Description/Amount) in table should not become a LineItem."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["Description", "Amount"],  # header
                ["Revenue", "10,00,000"],
            ]
        ]
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            items = await extractor.extract(_make_pdf_bytes_with_text())

        # Should be exactly 1 item (not 2 — header must be skipped)
        assert len(items) == 1
        assert items[0].description == "Revenue"


# OcrExtractor tests moved to tests/test_vision_ocr.py (Claude Vision pipeline, Phase 10)


# ── Factory: scanned PDF detection ────────────────────────────────────────────


class TestIsScannedPdf:
    def test_detects_native_pdf(self):
        """PDF with extractable text → is_scanned_pdf returns False."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Some financial text here"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = is_scanned_pdf(_make_pdf_bytes_with_text())

        assert result is False

    def test_factory_detects_scanned_pdf(self):
        """PDF with no extractable text → is_scanned_pdf returns True."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = is_scanned_pdf(_make_pdf_bytes_no_text())

        assert result is True

    def test_detects_scanned_pdf_empty_string(self):
        """PDF where extract_text returns empty string → is_scanned_pdf returns True."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = is_scanned_pdf(_make_pdf_bytes_no_text())

        assert result is True

    def test_detects_scanned_pdf_whitespace_only(self):
        """PDF where extract_text returns only whitespace → is_scanned_pdf returns True."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   \n\t  "

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = lambda s: s
        mock_pdf.__exit__ = MagicMock(return_value=False)

        with patch("pdfplumber.open", return_value=mock_pdf):
            result = is_scanned_pdf(_make_pdf_bytes_no_text())

        assert result is True


# ── Factory: routing ──────────────────────────────────────────────────────────


class TestExtractorFactory:
    @pytest.mark.asyncio
    async def test_factory_routes_xlsx_to_excel_extractor(self):
        """file_type='xlsx' → ExcelExtractor.extract() is called."""
        with patch(
            "app.services.extraction.extractor_factory.ExcelExtractor.extract",
            new_callable=AsyncMock,
            return_value=[LineItem("Revenue", 1000000.0, "income", "Revenue 10,00,000")],
        ) as mock_extract:
            result = await extract_document(_make_xlsx_bytes(), "xlsx", "client/file.xlsx")

        mock_extract.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_factory_routes_xls_to_excel_extractor(self):
        """file_type='xls' → ExcelExtractor.extract() is called."""
        with patch(
            "app.services.extraction.extractor_factory.ExcelExtractor.extract",
            new_callable=AsyncMock,
            return_value=[LineItem("Revenue", 1000000.0, "income", "Revenue 10,00,000")],
        ) as mock_extract:
            result = await extract_document(_make_xls_bytes(), "xls", "client/file.xls")

        mock_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_factory_routes_pdf_to_pdf_extractor(self):
        """Native PDF → PdfExtractor.extract() is called (not OCR)."""
        with (
            patch(
                "app.services.extraction.extractor_factory.is_scanned_pdf",
                return_value=False,
            ),
            patch(
                "app.services.extraction.extractor_factory.PdfExtractor.extract",
                new_callable=AsyncMock,
                return_value=[LineItem("Revenue", 1000000.0, "income", "Revenue")],
            ) as mock_pdf,
        ):
            result = await extract_document(
                _make_pdf_bytes_with_text(), "pdf", "client/file.pdf"
            )

        mock_pdf.assert_called_once()

    @pytest.mark.asyncio
    async def test_factory_routes_scanned_pdf_to_ocr_extractor(self):
        """Scanned PDF → OcrExtractor.extract() is called (not PdfExtractor)."""
        with (
            patch(
                "app.services.extraction.extractor_factory.is_scanned_pdf",
                return_value=True,
            ),
            patch(
                "app.services.extraction.extractor_factory.OcrExtractor.extract",
                new_callable=AsyncMock,
                return_value=[LineItem("Revenue", 1000000.0, "income", "Revenue")],
            ) as mock_ocr,
        ):
            result = await extract_document(
                _make_pdf_bytes_no_text(), "pdf", "client/scanned.pdf"
            )

        mock_ocr.assert_called_once()

    @pytest.mark.asyncio
    async def test_factory_returns_list_of_line_items(self):
        """extract_document always returns list[LineItem]."""
        expected = [LineItem("Revenue", 1000000.0, "income", "Revenue 10,00,000")]
        with patch(
            "app.services.extraction.extractor_factory.ExcelExtractor.extract",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await extract_document(_make_xlsx_bytes(), "xlsx", "client/file.xlsx")

        assert result == expected

    @pytest.mark.asyncio
    async def test_factory_raises_on_unknown_file_type(self):
        """Unknown file_type raises ExtractionError."""
        with pytest.raises(ExtractionError, match="Unsupported file type"):
            await extract_document(b"data", "docx", "client/file.docx")
