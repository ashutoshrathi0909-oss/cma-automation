"""Test full Vision OCR on FY22 Notes PDF."""
import asyncio
import logging
logging.basicConfig(level=logging.INFO)

async def test():
    with open("/tmp/test_notes.pdf", "rb") as f:
        content = f.read()

    from app.services.extraction.ocr_extractor import OcrExtractor, convert_from_bytes
    from app.services.extraction.page_filter import filter_pages

    images = convert_from_bytes(content)
    print(f"Pages: {len(images)}")
    content_pages = filter_pages(images)
    print(f"Content pages: {len(content_pages)}")

    extractor = OcrExtractor()
    items = await extractor.extract(content)

    print(f"\nTotal items extracted: {len(items)}")
    for i in items[:10]:
        print(f"  {i.description}: {i.amount}")

asyncio.run(test())
