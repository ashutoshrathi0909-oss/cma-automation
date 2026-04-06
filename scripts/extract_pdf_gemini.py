#!/usr/bin/env python3
"""
extract_pdf_gemini.py
=====================
Standalone script to extract financial data from a PDF using Gemini 2.5 Flash
via OpenRouter. Prints human-readable tables for manual verification.

Usage:
  python scripts/extract_pdf_gemini.py <path_to_pdf>

  # Or inside Docker:
  docker compose exec worker python scripts/extract_pdf_gemini.py /app/test.pdf

Requires: OPENROUTER_API_KEY in .env or environment
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
from pathlib import Path

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in .env or environment")
    sys.exit(1)

# ── Lazy imports (pdf2image needs poppler) ──────────────────────────────────
try:
    from pdf2image import convert_from_bytes
except ImportError:
    print("ERROR: pdf2image not installed. Run: pip install pdf2image")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai not installed. Run: pip install openai")
    sys.exit(1)

from PIL import Image

# ── Config ──────────────────────────────────────────────────────────────────
MODEL = "google/gemini-2.5-flash"
MAX_IMAGE_WIDTH = 1600
DPI = 200
MAX_PAGES_PER_BATCH = 5  # conservative for verification
MAX_TOKENS = 24000

# ── The same prompt from our production pipeline ────────────────────────────
SYSTEM_PROMPT = """You are a financial data extraction specialist for Indian CA firms.
You are analyzing scanned page images from Indian audited financial statements
(Balance Sheet, Profit & Loss Account, Trading Account, Notes to Accounts, Schedules).

YOUR TASK: Extract ALL financial line items with their amounts from each page image.

CRITICAL RULES:

1. EXTRACT ALL LINE ITEMS exactly as they appear in the document.
   Include every named financial item with a monetary amount. Do NOT skip items.

2. TRADING ACCOUNT: Indian firms often show a separate Trading Account before the P&L.
   Extract all lines from it.

3. TWO-COLUMN BALANCE SHEET (Liabilities | Assets): Extract each line item from
   BOTH columns separately. Do NOT merge left and right columns into one item.

4. P&L: Extract revenue categories, expense categories, profit/loss lines.
   Include individual product categories if they appear as line items.

5. GST LINES: Extract them normally. Do NOT skip. Do NOT confuse with sales revenue.

6. NOTES TO ACCOUNTS: Extract EVERY sub-item as a separate line item.
   NEVER collapse sub-items into their parent total.

7. INDIAN NUMBER FORMAT: "1,23,456" = 123456. Report amounts WITHOUT commas.

8. SCALE FACTOR: If page header says "in Lakhs" -> scale_factor = "in_lakhs".
   If "in Crores" -> "in_crores". Otherwise "absolute".

9. NEGATIVE AMOUNTS: Amounts in parentheses are negative: (1,23,456) = -123456.

10. SKIP PAGES: auditor's report, directors' report, Form 3CA/3CB,
    corporate information, accounting policies. Return empty items array.

11. SKIP: Addresses, phone numbers, GSTIN, PAN, signatures, bank account numbers.

12. SKIP BALANCING FIGURES: "To Gross Profit", "To Net Profit", "By Gross Profit", "By Net Profit".

13. SUB-LEDGER DETAIL PAGES: Extract ONLY the total line, not each individual name.

14. SECTIONS: income / expenses / assets / liabilities / equity / unknown

Respond with a single JSON object matching the provided schema. Do not include any text outside the JSON."""

EXTRACT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "page_results": {
            "type": "array",
            "description": "One entry per page.",
            "items": {
                "type": "object",
                "properties": {
                    "page_number": {"type": "integer"},
                    "page_type": {
                        "type": "string",
                        "enum": [
                            "profit_and_loss", "balance_sheet", "trading_account",
                            "notes_to_accounts", "schedules",
                            "auditor_report", "other_non_financial",
                        ],
                    },
                    "scale_factor": {
                        "type": "string",
                        "enum": ["absolute", "in_thousands", "in_lakhs", "in_crores"],
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "amount": {"type": "number"},
                                "section": {
                                    "type": "string",
                                    "enum": ["income", "expenses", "assets", "liabilities", "equity", "unknown"],
                                },
                                "ambiguity_question": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                },
                            },
                            "required": ["description", "amount", "section", "ambiguity_question"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["page_number", "page_type", "scale_factor", "items"],
                "additionalProperties": False,
            },
        },
        "currency_detected": {"type": "string"},
        "company_name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "financial_year": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": ["page_results", "currency_detected", "company_name", "financial_year"],
    "additionalProperties": False,
}


def image_to_base64(image: Image.Image) -> str:
    if image.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / image.width
        image = image.resize((MAX_IMAGE_WIDTH, int(image.height * ratio)), Image.LANCZOS)
    if image.mode != "RGB":
        image = image.convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def extract_pdf(pdf_path: str) -> dict:
    """Send PDF to Gemini 2.5 Flash via OpenRouter, return parsed JSON."""
    print(f"\n{'='*60}")
    print(f"  Extracting: {pdf_path}")
    print(f"  Model: {MODEL}")
    print(f"{'='*60}\n")

    # Convert PDF to images
    pdf_bytes = Path(pdf_path).read_bytes()
    poppler_path = os.environ.get("POPPLER_PATH") or None
    images = convert_from_bytes(pdf_bytes, dpi=DPI, poppler_path=poppler_path)
    print(f"  Converted to {len(images)} page images (DPI={DPI})")

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )

    all_page_results = []

    for batch_start in range(0, len(images), MAX_PAGES_PER_BATCH):
        batch = images[batch_start:batch_start + MAX_PAGES_PER_BATCH]
        batch_num = batch_start // MAX_PAGES_PER_BATCH + 1
        print(f"  Sending batch {batch_num} (pages {batch_start+1}-{batch_start+len(batch)})...")

        # Build content: images first, then instruction
        content = []
        for i, img in enumerate(batch):
            page_num = batch_start + i + 1
            content.append({"type": "text", "text": f"--- Page {page_num} ---"})
            b64 = image_to_base64(img)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })
        content.append({
            "type": "text",
            "text": "Extract all financial line items from the pages above. Respond with JSON only.",
        })

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "extract_financial_items",
                    "strict": True,
                    "schema": EXTRACT_JSON_SCHEMA,
                },
            },
        )

        # Check truncation
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "length":
            print(f"  WARNING: Batch {batch_num} was TRUNCATED (hit max_tokens)")

        # Parse response
        text = response.choices[0].message.content or ""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*\n?", "", text)
            text = re.sub(r"\n?```\s*$", "", text)
            text = text.strip()

        try:
            parsed = json.loads(text)
            batch_pages = parsed.get("page_results", [])
            all_page_results.extend(batch_pages)
            item_count = sum(len(p.get("items", [])) for p in batch_pages)
            print(f"  Batch {batch_num}: {len(batch_pages)} pages, {item_count} items extracted")

            # Capture metadata from first batch
            if batch_num == 1:
                company = parsed.get("company_name")
                fy = parsed.get("financial_year")
                currency = parsed.get("currency_detected", "INR")
        except json.JSONDecodeError as e:
            print(f"  ERROR: Failed to parse JSON from batch {batch_num}: {e}")
            print(f"  Raw content (first 300 chars): {text[:300]}")
            continue

    return {
        "page_results": all_page_results,
        "company_name": company if 'company' in dir() else None,
        "financial_year": fy if 'fy' in dir() else None,
        "currency_detected": currency if 'currency' in dir() else "INR",
    }


def get_scale_label(scale: str) -> str:
    return {
        "absolute": "",
        "in_thousands": " (in Thousands)",
        "in_lakhs": " (in Lakhs)",
        "in_crores": " (in Crores)",
    }.get(scale, "")


def get_scale_multiplier(scale: str) -> float:
    return {
        "absolute": 1.0,
        "in_thousands": 1_000.0,
        "in_lakhs": 100_000.0,
        "in_crores": 10_000_000.0,
    }.get(scale, 1.0)


def format_indian(amount: float) -> str:
    """Format number in Indian notation (e.g., 12,34,567.89)."""
    negative = amount < 0
    amount = abs(amount)
    integer_part = int(amount)
    decimal_part = amount - integer_part

    s = str(integer_part)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        groups.reverse()
        s = ",".join(groups) + "," + last3

    if decimal_part > 0.005:
        result = f"{s}.{decimal_part:.2f}"[2:]
        result = s + "." + f"{decimal_part:.2f}"[2:]
    else:
        result = s

    return f"({result})" if negative else result


def print_readable(data: dict):
    """Print extraction results in human-readable format."""
    print(f"\n{'='*70}")
    print(f"  EXTRACTION RESULTS — Gemini 2.5 Flash via OpenRouter")
    print(f"{'='*70}")
    if data.get("company_name"):
        print(f"  Company: {data['company_name']}")
    if data.get("financial_year"):
        print(f"  Financial Year: {data['financial_year']}")
    print(f"  Currency: {data.get('currency_detected', 'INR')}")
    print()

    total_items = 0
    ambiguous_items = []

    for page in data.get("page_results", []):
        page_num = page.get("page_number", "?")
        page_type = page.get("page_type", "unknown")
        scale = page.get("scale_factor", "absolute")
        items = page.get("items", [])

        if page_type in ("auditor_report", "other_non_financial"):
            print(f"  Page {page_num} — {page_type} (skipped)")
            continue

        if not items:
            print(f"  Page {page_num} — {page_type} (no items)")
            continue

        scale_label = get_scale_label(scale)
        print(f"  {'─'*66}")
        print(f"  Page {page_num} — {page_type.replace('_', ' ').title()}{scale_label}")
        print(f"  {'─'*66}")

        # Group by section
        sections = {}
        for item in items:
            sec = item.get("section", "unknown")
            sections.setdefault(sec, []).append(item)

        section_order = ["equity", "liabilities", "assets", "income", "expenses", "unknown"]
        for sec in section_order:
            if sec not in sections:
                continue
            sec_items = sections[sec]
            print(f"\n  {sec.upper()}")
            print(f"  {'No.':<5} {'Description':<45} {'Amount (Rs.)':>15}")
            print(f"  {'---':<5} {'-'*45:<45} {'-'*15:>15}")

            for i, item in enumerate(sec_items, 1):
                desc = item["description"][:44]
                amt = item["amount"]
                multiplier = get_scale_multiplier(scale)
                absolute_amt = amt * multiplier
                formatted = format_indian(absolute_amt)

                flag = ""
                if item.get("ambiguity_question"):
                    flag = " [?]"
                    ambiguous_items.append({
                        "page": page_num,
                        "description": item["description"],
                        "amount": formatted,
                        "question": item["ambiguity_question"],
                    })

                print(f"  {i:<5} {desc:<45} {formatted:>15}{flag}")
                total_items += 1

    # Summary
    print(f"\n  {'='*66}")
    print(f"  SUMMARY")
    print(f"  {'='*66}")
    print(f"  Total items extracted: {total_items}")
    print(f"  Total pages: {len(data.get('page_results', []))}")

    if ambiguous_items:
        print(f"\n  AMBIGUOUS ITEMS ({len(ambiguous_items)}):")
        for a in ambiguous_items:
            print(f"    Page {a['page']} | {a['description']} | Rs. {a['amount']}")
            print(f"      Question: {a['question']}")

    print()

    # Also save raw JSON for comparison
    out_path = Path(pdf_path).with_suffix(".extraction.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Raw JSON saved to: {out_path}")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_pdf_gemini.py <path_to_pdf>")
        print("Example: python scripts/extract_pdf_gemini.py 'DOCS/BSheet.pdf'")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    data = extract_pdf(pdf_path)
    print_readable(data)
