"""
Phase 2: Baseline classification — sends all 352 deduped items to Haiku via OpenRouter.
Replicates the exact prompt template from prompt-tuning-execution.md.
Outputs baseline_results.json.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load env from project root
PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not set in .env")
    sys.exit(1)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4-5"
BATCH_SIZE = 15
OUTPUT_DIR = Path(__file__).parent

# Read CMA fields
CMA_FIELDS_FILE = OUTPUT_DIR / "cma_fields_formatted.txt"
CMA_FIELDS = CMA_FIELDS_FILE.read_text(encoding="utf-8").strip()

# Read deduped items
DEDUPED_FILE = OUTPUT_DIR / "deduped_items.json"
with open(DEDUPED_FILE, "r", encoding="utf-8") as f:
    deduped_data = json.load(f)

unique_items = deduped_data["unique_items"]
print(f"Loaded {len(unique_items)} unique items")


def build_batch_prompt(items):
    """Build the exact Phase 2 prompt template from execution doc."""
    items_text = ""
    for i, item in enumerate(items, 1):
        amt = item["amount_rupees"]
        amt_str = f"Rs {amt:,.2f}" if amt is not None else "not provided"
        items_text += f"""
Item {i}:
  Description: {item['raw_text']}
  Amount: {amt_str}
  Section: {item.get('section', 'not specified')}
  Sheet: {item.get('sheet_name', 'not specified')}
  Financial Year: {item.get('financial_year', 'not specified')}
"""

    prompt = f"""You are a financial analyst classifying line items for Indian CMA (Credit Monitoring Arrangement) documents.

I will give you {len(items)} line items. For EACH item, classify it into exactly ONE CMA field.

COMPANY: BCIPL (Bagadia Chaitra Industries Private Limited)
INDUSTRY: Manufacturing (metal stamping, laminations, CRCA components)
DOCUMENT TYPE: Combined Financial Statement

VALID CMA FIELDS (use EXACT field name and row number):
{CMA_FIELDS}

CLASSIFICATION RULES:
1. Match each line item to the SINGLE most appropriate CMA field from the list above
2. Use the EXACT field name from the list — do not invent new names
3. Set confidence 0.0-1.0 based on certainty
4. If confidence < 0.8, set is_uncertain=true and explain why
5. NEVER guess silently — flag uncertainty
6. Consider industry type: Manufacturing firms have production-related expenses
7. The "section" and "sheet_name" tell you WHERE in the financial statement this item appeared — use this context
8. Items from "Notes to P & L" are income/expense items
9. Items from "Notes BS" are asset/liability items
10. Items from depreciation schedules are usually Row 56 (manufacturing) or Row 63 (admin)

LINE ITEMS TO CLASSIFY:
{items_text}
Return a JSON array with your classification for each item. Use this exact format:
[
  {{
    "item_index": 1,
    "raw_text": "exact raw_text from above",
    "classified_cma_field": "Exact CMA Field Name",
    "classified_cma_row": 42,
    "confidence": 0.95,
    "is_uncertain": false,
    "reasoning": "Brief 1-sentence reason"
  }},
  ...
]

IMPORTANT: Return ONLY the JSON array. No other text."""
    return prompt


def call_haiku(prompt, batch_num, retry=False):
    """Call Haiku via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cma-automation.local",
        "X-Title": "CMA Prompt Tuning"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 4096,
    }

    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        # Parse JSON from response — handle markdown code blocks
        text = content.strip()
        if text.startswith("```"):
            # Remove markdown code block wrapper
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)

        results = json.loads(text)
        return results, usage

    except json.JSONDecodeError as e:
        if not retry:
            print(f"  Batch {batch_num}: JSON parse error, retrying... ({e})")
            time.sleep(2)
            return call_haiku(prompt, batch_num, retry=True)
        else:
            print(f"  Batch {batch_num}: FAILED to parse JSON after retry: {e}")
            print(f"  Raw response: {content[:500]}")
            return None, {}
    except Exception as e:
        if not retry:
            print(f"  Batch {batch_num}: API error, retrying... ({e})")
            time.sleep(5)
            return call_haiku(prompt, batch_num, retry=True)
        else:
            print(f"  Batch {batch_num}: FAILED after retry: {e}")
            return None, {}


def main():
    # Create batches
    batches = []
    for i in range(0, len(unique_items), BATCH_SIZE):
        batches.append(unique_items[i:i + BATCH_SIZE])
    print(f"Created {len(batches)} batches of {BATCH_SIZE}")

    all_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    failed_batches = []

    for batch_num, batch_items in enumerate(batches):
        print(f"Batch {batch_num}/{len(batches)-1} ({len(batch_items)} items)...", end=" ", flush=True)

        prompt = build_batch_prompt(batch_items)
        results, usage = call_haiku(prompt, batch_num)

        input_tok = usage.get("prompt_tokens", 0)
        output_tok = usage.get("completion_tokens", 0)
        total_input_tokens += input_tok
        total_output_tokens += output_tok

        if results is None:
            print(f"FAILED")
            failed_batches.append(batch_num)
            # Add placeholder results
            for item in batch_items:
                all_results.append({
                    "raw_text": item["raw_text"],
                    "financial_year": item["financial_year"],
                    "section": item.get("section", ""),
                    "sheet_name": item.get("sheet_name", ""),
                    "expected_cma_field": item["correct_cma_field"],
                    "expected_cma_row": item["correct_cma_row"],
                    "predicted_cma_field": "ERROR",
                    "predicted_cma_row": -1,
                    "confidence": 0.0,
                    "is_correct": False,
                    "reasoning": "API call failed"
                })
            continue

        # Match results back to items
        for item in batch_items:
            # Find matching result by raw_text or index
            matched = None
            for r in results:
                if r.get("raw_text", "").strip().lower() == item["raw_text"].strip().lower():
                    matched = r
                    break
            if not matched and results:
                # Fall back to index-based matching
                idx = batch_items.index(item)
                if idx < len(results):
                    matched = results[idx]

            if matched:
                pred_row = matched.get("classified_cma_row", -1)
                all_results.append({
                    "raw_text": item["raw_text"],
                    "financial_year": item["financial_year"],
                    "section": item.get("section", ""),
                    "sheet_name": item.get("sheet_name", ""),
                    "expected_cma_field": item["correct_cma_field"],
                    "expected_cma_row": item["correct_cma_row"],
                    "predicted_cma_field": matched.get("classified_cma_field", "UNKNOWN"),
                    "predicted_cma_row": pred_row,
                    "confidence": matched.get("confidence", 0.0),
                    "is_correct": pred_row == item["correct_cma_row"],
                    "reasoning": matched.get("reasoning", "")
                })
            else:
                all_results.append({
                    "raw_text": item["raw_text"],
                    "financial_year": item["financial_year"],
                    "section": item.get("section", ""),
                    "sheet_name": item.get("sheet_name", ""),
                    "expected_cma_field": item["correct_cma_field"],
                    "expected_cma_row": item["correct_cma_row"],
                    "predicted_cma_field": "UNMATCHED",
                    "predicted_cma_row": -1,
                    "confidence": 0.0,
                    "is_correct": False,
                    "reasoning": "Could not match result to item"
                })

        correct = sum(1 for r in results if any(
            r.get("classified_cma_row") == item["correct_cma_row"]
            for item in batch_items
            if r.get("raw_text", "").strip().lower() == item["raw_text"].strip().lower()
        ))
        print(f"OK (in={input_tok}, out={output_tok})")

        # Rate limit: small delay between batches
        time.sleep(1)

    # Build output
    n_items = len(all_results)
    correct_count = sum(1 for r in all_results if r["is_correct"])

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "baseline (from ai_classifier.py)",
        "total_items": n_items,
        "correct": correct_count,
        "accuracy_pct": round(correct_count / n_items * 100, 1) if n_items else 0,
        "failed_batches": failed_batches,
        "results": all_results,
        "token_estimate": {
            "avg_input_tokens_per_item": round(total_input_tokens / n_items) if n_items else 0,
            "avg_output_tokens_per_item": round(total_output_tokens / n_items) if n_items else 0,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_batches": len(batches),
        }
    }

    out_file = OUTPUT_DIR / "baseline_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"BASELINE COMPLETE")
    print(f"Total items: {n_items}")
    print(f"Correct: {correct_count} ({output['accuracy_pct']}%)")
    print(f"Wrong: {n_items - correct_count}")
    print(f"Failed batches: {len(failed_batches)}")
    print(f"Total tokens: {total_input_tokens} in + {total_output_tokens} out")
    print(f"Results saved to: {out_file}")


if __name__ == "__main__":
    main()
