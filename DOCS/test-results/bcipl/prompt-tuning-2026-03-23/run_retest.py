"""
Phase 6: Re-test ALL items with revised prompt V1.
Compares against baseline to measure improvement.
Outputs retest_v1_results.json
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4-5"
BATCH_SIZE = 15
OUTPUT_DIR = Path(__file__).parent

# Read revised prompt template
REVISED_PROMPT = (OUTPUT_DIR / "revised_prompt_v1.txt").read_text(encoding="utf-8")

# Read deduped items
with open(OUTPUT_DIR / "deduped_items.json", "r", encoding="utf-8") as f:
    deduped_data = json.load(f)

unique_items = deduped_data["unique_items"]
print(f"Loaded {len(unique_items)} unique items")


def build_batch_prompt(items):
    """Build prompt using revised V1 template."""
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

    # Replace {N} in template and append items
    prompt = REVISED_PROMPT.replace("{N}", str(len(items)))

    # Insert items before the output format section
    marker = "=== OUTPUT FORMAT ==="
    parts = prompt.split(marker)
    prompt = parts[0] + f"\nLINE ITEMS TO CLASSIFY:\n{items_text}\n" + marker + parts[1]

    return prompt


def call_haiku(prompt, batch_num, retry=False):
    """Call Haiku via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cma-automation.local",
        "X-Title": "CMA Prompt Tuning V1"
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

        text = content.strip()
        if text.startswith("```"):
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
            print(f"  Batch {batch_num}: JSON error, retrying...")
            time.sleep(2)
            return call_haiku(prompt, batch_num, retry=True)
        else:
            print(f"  Batch {batch_num}: FAILED JSON: {e}")
            print(f"  Raw: {content[:300]}")
            return None, {}
    except Exception as e:
        if not retry:
            print(f"  Batch {batch_num}: API error, retrying...")
            time.sleep(5)
            return call_haiku(prompt, batch_num, retry=True)
        else:
            print(f"  Batch {batch_num}: FAILED: {e}")
            return None, {}


def main():
    # Load baseline for comparison
    with open(OUTPUT_DIR / "baseline_results.json", "r", encoding="utf-8") as f:
        baseline = json.load(f)
    baseline_map = {r["raw_text"]: r for r in baseline["results"]}

    # Create batches
    batches = []
    for i in range(0, len(unique_items), BATCH_SIZE):
        batches.append(unique_items[i:i + BATCH_SIZE])
    print(f"Created {len(batches)} batches")

    all_results = []
    total_input_tokens = 0
    total_output_tokens = 0
    failed_batches = []

    for batch_num, batch_items in enumerate(batches):
        print(f"Batch {batch_num}/{len(batches)-1} ({len(batch_items)} items)...", end=" ", flush=True)

        prompt = build_batch_prompt(batch_items)
        results, usage = call_haiku(prompt, batch_num)

        total_input_tokens += usage.get("prompt_tokens", 0)
        total_output_tokens += usage.get("completion_tokens", 0)

        if results is None:
            print("FAILED")
            failed_batches.append(batch_num)
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

        for item in batch_items:
            matched = None
            for r in results:
                if r.get("raw_text", "").strip().lower() == item["raw_text"].strip().lower():
                    matched = r
                    break
            if not matched and results:
                idx = batch_items.index(item)
                if idx < len(results):
                    matched = results[idx]

            if matched:
                pred_row = matched.get("classified_cma_row", -1)
                bl = baseline_map.get(item["raw_text"], {})
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
                    "reasoning": matched.get("reasoning", ""),
                    "baseline_was_correct": bl.get("is_correct", False),
                    "baseline_predicted_row": bl.get("predicted_cma_row", -1),
                })
            else:
                bl = baseline_map.get(item["raw_text"], {})
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
                    "reasoning": "Could not match result to item",
                    "baseline_was_correct": bl.get("is_correct", False),
                    "baseline_predicted_row": bl.get("predicted_cma_row", -1),
                })

        print(f"OK (in={usage.get('prompt_tokens', 0)}, out={usage.get('completion_tokens', 0)})")
        time.sleep(1)

    # Compute comparison metrics
    n = len(all_results)
    v1_correct = sum(1 for r in all_results if r["is_correct"])
    bl_correct = baseline["correct"]

    # Items that were wrong in baseline
    bl_wrong_items = [r for r in all_results if not r.get("baseline_was_correct", True)]
    recovered = sum(1 for r in bl_wrong_items if r["is_correct"])

    # Items that were correct in baseline but now wrong (regressions)
    regressions = [r for r in all_results if r.get("baseline_was_correct", False) and not r["is_correct"]]

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": "revised_v1",
        "total_items": n,
        "correct": v1_correct,
        "accuracy_pct": round(v1_correct / n * 100, 1) if n else 0,
        "baseline_correct": bl_correct,
        "baseline_accuracy_pct": round(bl_correct / n * 100, 1) if n else 0,
        "improvement_pct_points": round((v1_correct - bl_correct) / n * 100, 1) if n else 0,
        "previously_wrong": len(bl_wrong_items),
        "recovered": recovered,
        "recovery_rate_pct": round(recovered / len(bl_wrong_items) * 100, 1) if bl_wrong_items else 0,
        "regressions": len(regressions),
        "regression_details": [
            {
                "raw_text": r["raw_text"],
                "expected_row": r["expected_cma_row"],
                "baseline_row": r.get("baseline_predicted_row"),
                "v1_row": r["predicted_cma_row"]
            }
            for r in regressions
        ],
        "failed_batches": failed_batches,
        "results": all_results,
        "token_estimate": {
            "avg_input_tokens_per_item": round(total_input_tokens / n) if n else 0,
            "avg_output_tokens_per_item": round(total_output_tokens / n) if n else 0,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }
    }

    out_file = OUTPUT_DIR / "retest_v1_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*55}")
    print(f"RE-TEST RESULTS (Prompt V1)")
    print(f"{'='*55}")
    print(f"Previously failed items: {len(bl_wrong_items)}")
    print(f"Now correct: {recovered} ({output['recovery_rate_pct']}% recovery)")
    print(f"Still wrong: {len(bl_wrong_items) - recovered}")
    print(f"Regressions (were correct, now wrong): {len(regressions)}")
    print(f"")
    print(f"Overall accuracy:")
    print(f"  Baseline: {bl_correct}/{n} ({output['baseline_accuracy_pct']}%)")
    print(f"  After V1: {v1_correct}/{n} ({output['accuracy_pct']}%)")
    print(f"  Improvement: {output['improvement_pct_points']:+.1f} percentage points")
    print(f"")
    print(f"Tokens: {total_input_tokens} in + {total_output_tokens} out")
    print(f"Saved to: {out_file}")

    if regressions:
        print(f"\nREGRESSIONS:")
        for r in regressions:
            print(f"  {r['raw_text'][:50]}: expected={r['expected_row']}, baseline={r.get('baseline_predicted_row')}, v1={r['predicted_cma_row']}")


if __name__ == "__main__":
    main()
