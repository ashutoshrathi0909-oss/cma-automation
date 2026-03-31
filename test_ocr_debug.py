"""Debug Vision OCR - test pages 1-5 to see why batch fails."""
import asyncio
import logging
logging.basicConfig(level=logging.INFO)
import json

async def test():
    with open("/tmp/test_notes.pdf", "rb") as f:
        content = f.read()

    from app.services.extraction.ocr_extractor import convert_from_bytes, _image_to_base64
    from app.services.extraction.page_filter import filter_pages
    from app.services.extraction.vision_prompt import EXTRACT_TOOL_SCHEMA, SYSTEM_PROMPT
    from app.config import get_settings
    import anthropic

    images = convert_from_bytes(content)
    content_pages = filter_pages(images)

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Test pages 1-5
    batch = content_pages[:5]
    content_msg = []
    for page_num, image in batch:
        content_msg.append({"type": "text", "text": f"--- Page {page_num} ---"})
        content_msg.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": _image_to_base64(image),
            },
        })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        tools=[EXTRACT_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "extract_financial_items"},
        messages=[{"role": "user", "content": content_msg}],
    )

    for block in response.content:
        block_type = getattr(block, "type", "unknown")
        print(f"Block type: {block_type}")
        if block_type == "tool_use":
            data = block.input
            page_results = data.get("page_results", [])
            print(f"page_results count: {len(page_results)}")
            for pr in page_results:
                pg_num = pr.get("page_number")
                pg_type = pr.get("page_type")
                items = pr.get("items", [])
                print(f"  page {pg_num}: type={pg_type}, items={len(items)}")
                for item in items[:3]:
                    print(f"    {item.get('description')}: {item.get('amount')}")

asyncio.run(test())
