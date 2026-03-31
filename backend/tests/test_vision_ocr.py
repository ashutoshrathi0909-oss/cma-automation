"""Tests for OcrExtractor — Claude Vision pipeline."""
import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image

from app.services.extraction.ocr_extractor import OcrExtractor, _image_to_base64, _get_scale_multiplier
from app.services.extraction._types import LineItem, ExtractionError


def make_content_image() -> Image.Image:
    """Helper: create a non-blank test image."""
    from PIL import ImageDraw
    img = Image.new("RGB", (400, 600), "white")
    ImageDraw.Draw(img).text((10, 10), "Revenue 1,00,000", fill="black")
    return img


def make_tool_response(items: list[dict], page_type: str = "profit_and_loss", scale: str = "absolute"):
    """Helper: create a mock Claude tool_use response."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.input = {
        "page_results": [{
            "page_number": 1,
            "page_type": page_type,
            "scale_factor": scale,
            "items": items,
        }],
        "currency_detected": "INR",
        "company_name": "Test Co",
        "financial_year": "2023-24",
    }
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    return mock_response


class TestImageToBase64:
    def test_returns_string(self):
        img = Image.new("RGB", (100, 100), "white")
        result = _image_to_base64(img)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_resizes_large_image(self):
        img = Image.new("RGB", (3000, 4000), "white")
        _image_to_base64(img)  # Should not raise

    def test_converts_rgba_to_rgb(self):
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 128))
        result = _image_to_base64(img)
        assert isinstance(result, str)


class TestGetScaleMultiplier:
    def test_absolute(self):
        assert _get_scale_multiplier("absolute") == 1.0

    def test_in_lakhs(self):
        assert _get_scale_multiplier("in_lakhs") == 100_000.0

    def test_in_crores(self):
        assert _get_scale_multiplier("in_crores") == 10_000_000.0

    def test_in_thousands(self):
        assert _get_scale_multiplier("in_thousands") == 1_000.0

    def test_unknown_defaults_to_absolute(self):
        assert _get_scale_multiplier("unknown") == 1.0


class TestOcrExtractor:
    def test_uses_sonnet_model(self):
        from app.services.extraction.ocr_extractor import ANTHROPIC_VISION_MODEL
        assert ANTHROPIC_VISION_MODEL == "claude-sonnet-4-6"

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    def test_empty_document_returns_empty_list(self, mock_filter, mock_convert):
        mock_convert.return_value = []
        mock_filter.return_value = []
        extractor = OcrExtractor()
        result = asyncio.run(extractor.extract(b"fake pdf"))
        assert result == []

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_extracts_line_items_from_response(self, mock_anthropic, mock_filter, mock_convert):
        mock_convert.return_value = [make_content_image()]
        mock_filter.return_value = [(1, make_content_image())]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = make_tool_response([
            {"description": "Revenue from Operations", "amount": 1000000, "section": "income", "ambiguity_question": None},
            {"description": "Cost of Materials", "amount": 800000, "section": "expenses", "ambiguity_question": None},
        ])

        extractor = OcrExtractor()
        result = asyncio.run(extractor.extract(b"fake pdf"))

        assert len(result) == 2
        assert result[0].description == "Revenue from Operations"
        assert result[0].amount == 1000000.0
        assert result[1].description == "Cost of Materials"

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_scale_factor_lakhs_applied(self, mock_anthropic, mock_filter, mock_convert):
        mock_convert.return_value = [make_content_image()]
        mock_filter.return_value = [(1, make_content_image())]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = make_tool_response(
            [{"description": "Sales", "amount": 55.0, "section": "income", "ambiguity_question": None}],
            scale="in_lakhs",
        )

        extractor = OcrExtractor()
        result = asyncio.run(extractor.extract(b"fake pdf"))
        assert result[0].amount == 55.0 * 100_000

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_ambiguity_question_preserved(self, mock_anthropic, mock_filter, mock_convert):
        mock_convert.return_value = [make_content_image()]
        mock_filter.return_value = [(1, make_content_image())]

        question = "Please split: Factory Wages (Row 45) | Other Mfg Expenses (Row 49)"
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = make_tool_response([
            {"description": "Wages & Other Expenses", "amount": 2550000, "section": "expenses",
             "ambiguity_question": question},
        ])

        extractor = OcrExtractor()
        result = asyncio.run(extractor.extract(b"fake pdf"))
        assert result[0].ambiguity_question == question

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_auditor_report_pages_skipped(self, mock_anthropic, mock_filter, mock_convert):
        mock_convert.return_value = [make_content_image()]
        mock_filter.return_value = [(1, make_content_image())]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = make_tool_response(
            [{"description": "Audit Opinion", "amount": 0, "section": "", "ambiguity_question": None}],
            page_type="auditor_report",
        )

        extractor = OcrExtractor()
        result = asyncio.run(extractor.extract(b"fake pdf"))
        assert result == []  # auditor_report pages produce no items

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_no_tool_block_returns_empty(self, mock_anthropic, mock_filter, mock_convert):
        mock_convert.return_value = [make_content_image()]
        mock_filter.return_value = [(1, make_content_image())]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = []  # no tool_use block
        mock_client.messages.create.return_value = mock_response

        extractor = OcrExtractor()
        result = asyncio.run(extractor.extract(b"fake pdf"))
        assert result == []

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    def test_pdf_conversion_failure_raises_extraction_error(self, mock_convert):
        mock_convert.side_effect = Exception("poppler not found")

        extractor = OcrExtractor()
        with pytest.raises(ExtractionError):
            asyncio.run(extractor.extract(b"fake pdf"))

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_batching_splits_large_page_sets(self, mock_anthropic, mock_filter, mock_convert):
        """20 content pages should result in 2 API calls (batch size 15)."""
        imgs = [make_content_image() for _ in range(20)]
        mock_convert.return_value = imgs
        mock_filter.return_value = [(i + 1, img) for i, img in enumerate(imgs)]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = make_tool_response([])

        extractor = OcrExtractor()
        asyncio.run(extractor.extract(b"fake pdf"))

        assert mock_client.messages.create.call_count == 2  # 15 + 5

    @patch("app.services.extraction.ocr_extractor.convert_from_bytes")
    @patch("app.services.extraction.ocr_extractor.filter_pages")
    @patch("app.services.extraction.ocr_extractor.anthropic.Anthropic")
    def test_sonnet_model_used_in_api_call(self, mock_anthropic, mock_filter, mock_convert):
        mock_convert.return_value = [make_content_image()]
        mock_filter.return_value = [(1, make_content_image())]

        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = make_tool_response([])

        extractor = OcrExtractor()
        asyncio.run(extractor.extract(b"fake pdf"))

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs.get("model") == "claude-sonnet-4-6"


class TestLineItemAmbiguityQuestion:
    def test_default_none(self):
        item = LineItem(description="Revenue", amount=1000000.0, section="income", raw_text="Revenue  10,00,000")
        assert item.ambiguity_question is None

    def test_can_be_set(self):
        item = LineItem(
            description="Wages & Other",
            amount=2550000.0,
            section="expenses",
            raw_text="Wages & Other  25,50,000",
            ambiguity_question="Split: Wages (Row 45) | Other (Row 49)",
        )
        assert "Row 45" in item.ambiguity_question
