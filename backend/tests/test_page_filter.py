"""Tests for page_filter.py — blank page detection."""
import pytest
from PIL import Image, ImageDraw
from app.services.extraction.page_filter import has_content, filter_pages


class TestHasContent:
    def test_blank_white_image_returns_false(self):
        img = Image.new("RGB", (200, 300), "white")
        assert has_content(img) is False

    def test_blank_black_image_returns_false(self):
        img = Image.new("RGB", (200, 300), "black")
        assert has_content(img) is False

    def test_image_with_text_returns_true(self):
        img = Image.new("RGB", (200, 300), "white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Revenue from Operations  56,47,000", fill="black")
        draw.text((10, 30), "Less: Cost of Goods Sold  42,00,000", fill="black")
        assert has_content(img) is True

    def test_image_with_table_lines_returns_true(self):
        img = Image.new("RGB", (200, 300), "white")
        draw = ImageDraw.Draw(img)
        for y in range(10, 290, 20):
            draw.line([(0, y), (200, y)], fill="black", width=1)
        assert has_content(img) is True

    def test_empty_image_returns_false(self):
        img = Image.new("RGB", (1, 1), "white")
        assert has_content(img) is False


class TestFilterPages:
    def test_returns_only_content_pages(self):
        blank = Image.new("RGB", (200, 300), "white")
        content = Image.new("RGB", (200, 300), "white")
        ImageDraw.Draw(content).text((10, 10), "Balance Sheet", fill="black")

        result = filter_pages([blank, content, blank])
        assert len(result) == 1

    def test_page_numbers_are_1_indexed(self):
        blank = Image.new("RGB", (200, 300), "white")
        content = Image.new("RGB", (200, 300), "white")
        ImageDraw.Draw(content).text((10, 10), "P&L Account", fill="black")

        result = filter_pages([blank, content])
        assert result[0][0] == 2  # page_number is 2, not 1

    def test_all_blank_returns_empty(self):
        blank = Image.new("RGB", (200, 300), "white")
        result = filter_pages([blank, blank, blank])
        assert result == []

    def test_all_content_returns_all(self):
        imgs = []
        for _ in range(3):
            img = Image.new("RGB", (200, 300), "white")
            ImageDraw.Draw(img).text((10, 10), "Financial data here", fill="black")
            imgs.append(img)
        result = filter_pages(imgs)
        assert len(result) == 3
        assert [r[0] for r in result] == [1, 2, 3]
