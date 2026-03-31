"""Debug Vision OCR - test all 15 pages to see truncation."""
import asyncio
import logging
logging.basicConfig(level=logging.INFO)

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

    # Test pages 1-15
    batch = content_pages[:15]
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

    print(f"Sending {len(batch)} pages...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        tools=[EXTRACT_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "extract_financial_items"},
        messages=[{"role": "user", "content": content_msg}],
    )

    print(f"Stop reason: {response.stop_reason}")
    print(f"Input tokens: {response.usage.input_tokens}")
    print(f"Output tokens: {response.usage.output_tokens}")

    for block in response.content:
        block_type = getattr(block, "type", "unknown")
        print(f"Block type: {block_type}")
        if block_type == "tool_use":
            data = block.input
            page_results = data.get("page_results", [])
            print(f"page_results count: {len(page_results)}")
            total_items = 0
            for pr in page_results:
                pg_num = pr.get("page_number")
                pg_type = pr.get("page_type")
                items = pr.get("items", [])
                total_items += len(items)
                print(f"  page {pg_num}: type={pg_type}, items={len(items)}")
            print(f"Total items: {total_items}")

asyncio.run(test())
