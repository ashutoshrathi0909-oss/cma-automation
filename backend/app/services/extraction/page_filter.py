"""
page_filter.py
==============
Lightweight pre-filter to skip blank/empty pages before sending to Claude Vision.
Only skips pages that are completely blank (solid color / no printed content).
Financial vs non-financial detection is handled by Claude Vision itself.
"""
from __future__ import annotations

import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Pages with pixel std deviation below this threshold are considered blank.
# Solid white/black pages → std ≈ 0. Any printed content → std >> 5.
_MIN_STD_DEV = 5.0


def has_content(image: Image.Image) -> bool:
    """Return True if the page image appears to contain printed content.

    Uses pixel standard deviation: a blank/solid page has std ~0,
    while a page with text/tables has std >> 15.
    Resizes to a tiny thumbnail for fast computation.
    """
    thumb = image.copy()
    thumb.thumbnail((100, 150))
    grayscale = thumb.convert("L")
    pixels = list(grayscale.getdata())

    if not pixels:
        return False

    mean = sum(pixels) / len(pixels)
    variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
    std_dev = variance ** 0.5

    return std_dev > _MIN_STD_DEV


def filter_pages(images: list[Image.Image]) -> list[tuple[int, Image.Image]]:
    """Return (page_number, image) tuples for pages that have content.

    page_number is 1-indexed to match PDF page numbering.
    """
    result = []
    for idx, img in enumerate(images):
        page_num = idx + 1
        if has_content(img):
            result.append((page_num, img))
        else:
            logger.info("Skipping blank page %d", page_num)
    return result
