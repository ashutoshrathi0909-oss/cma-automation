"""
Phase 4: Pattern interviews — ask Haiku WHY it made specific errors.
One API call per failure pattern (patterns with 3+ items).
Outputs interview_responses.json
"""
import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-haiku-4-5"
OUTPUT_DIR = Path(__file__).parent

# Load baseline results
with open(OUTPUT_DIR / "baseline_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]
wrong = [r for r in results if not r["is_correct"]]

# Group failures by pattern (same logic as analysis script)
from collections import defaultdict
patterns = defaultdict(list)

for r in wrong:
    exp_row = r["expected_cma_row"]
    pred_row = r["predicted_cma_row"]

    exp_is_pnl = exp_row <= 108
    pred_is_pnl = pred_row <= 108 if pred_row > 0 else False
    if exp_is_pnl != pred_is_pnl and pred_row > 0:
        patterns["Section confusion (P&L vs BS)"].append(r)
        continue
    if pred_row > 0 and abs(exp_row - pred_row) <= 5:
        patterns["Adjacent field (within 5 rows)"].append(r)
        continue
    if exp_row in (56, 63, 162, 163, 165, 175) or pred_row in (56, 63, 162, 163, 165, 175):
        patterns["Depreciation / Fixed asset routing"].append(r)
        continue
    if exp_row in (83, 84, 85) or pred_row in (83, 84, 85):
        patterns["Interest routing (term/WC/bank)"].append(r)
        continue
    others_rows = {34, 49, 64, 71, 93, 125, 238, 250}
    if pred_row in others_rows:
        patterns["Others overflow"].append(r)
        continue
    if exp_row in (193, 194, 197, 198, 200, 201) or pred_row in (193, 194, 197, 198, 200, 201):
        patterns["Inventory / stock confusion"].append(r)
        continue
    if exp_row in (242, 243, 249, 250) or pred_row in (242, 243, 249, 250):
        patterns["Creditors / payables routing"].append(r)
        continue
    if exp_row in (244, 246) or pred_row in (244, 246):
        patterns["Statutory dues / provisions"].append(r)
        continue
    if exp_row in (131, 132, 136, 137, 148, 149, 152, 153, 154) or \
       pred_row in (131, 132, 136, 137, 148, 149, 152, 153, 154):
        patterns["Loan classification"].append(r)
        continue
    if exp_row in (219, 220, 221, 222, 223, 224, 235, 236, 237) or \
       pred_row in (219, 220, 221, 222, 223, 224, 235, 236, 237):
        patterns["Advances / receivables routing"].append(r)
        continue
    if exp_row in (45, 67, 73) or pred_row in (45, 67, 73):
        patterns["Employee expense routing"].append(r)
        continue
    patterns["Other"].append(r)

# Filter to patterns with 3+ items
interview_patterns = {k: v for k, v in patterns.items() if len(v) >= 3}
print(f"Patterns with 3+ items: {len(interview_patterns)}")
for name, items in sorted(interview_patterns.items(), key=lambda x: -len(x[1])):
    print(f"  {name}: {len(items)} items")


def build_interview_prompt(pattern_name, items):
    """Build the Phase 4 interview prompt."""
    items_text = ""
    for i, r in enumerate(items[:10], 1):  # max 10 examples
        items_text += f"""
{i}. "{r['raw_text']}" (Sheet: {r['sheet_name']}, Section: {r['section']})
   Your answer: {r['predicted_cma_field']} (Row {r['predicted_cma_row']})
   Correct answer: {r['expected_cma_field']} (Row {r['expected_cma_row']})
"""

    return f"""You are a financial analyst who classifies Indian CMA line items.
You classified some items INCORRECTLY. I need to understand WHY so I can improve the classification prompt.

FAILURE PATTERN: {pattern_name}

ITEMS YOU GOT WRONG:
{items_text}
QUESTIONS -- answer each one:

1. PROMPT WEAKNESS: What in the classification prompt made you choose the wrong field? Was there ambiguity? Missing context?

2. MISSING KNOWLEDGE: What additional information would have helped you get ALL of these right? Be specific -- what exact sentence or rule should be in the prompt?

3. DETERMINISTIC RULE: Is there a simple pattern-matching rule that could classify ALL items in this group correctly WITHOUT needing AI?
   Format: IF description contains [X] AND section contains [Y] THEN cma_row = [Z]
   (These become Rule Engine rules that skip AI entirely, saving cost)

4. SECTION SIGNAL: Did the "section" and "sheet_name" fields help or confuse you? How should they be used?

5. FIELD GROUPING: Would it help if the 139 CMA fields were grouped by category (P&L Income, P&L Manufacturing Expenses, P&L Admin Expenses, BS Assets, BS Liabilities) instead of a flat numbered list?

Return your answers as structured JSON:
{{
  "pattern": "{pattern_name}",
  "prompt_weakness": "...",
  "missing_knowledge": "...",
  "deterministic_rules": [
    {{
      "condition": "IF description contains 'X' AND section contains 'Y'",
      "cma_field": "...",
      "cma_row": 42,
      "covers_items": [1, 2, 3]
    }}
  ],
  "section_signal_feedback": "...",
  "field_grouping_feedback": "...",
  "suggested_prompt_additions": ["sentence 1 to add", "sentence 2 to add"]
}}

IMPORTANT: Return ONLY the JSON object. No other text."""


def call_haiku(prompt, pattern_name, retry=False):
    """Call Haiku via OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cma-automation.local",
        "X-Title": "CMA Prompt Tuning - Interview"
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

        result = json.loads(text)
        return result, usage

    except json.JSONDecodeError as e:
        if not retry:
            print(f"  {pattern_name}: JSON error, retrying...")
            time.sleep(2)
            return call_haiku(prompt, pattern_name, retry=True)
        else:
            print(f"  {pattern_name}: FAILED JSON parse: {e}")
            print(f"  Raw: {content[:300]}")
            return {"pattern": pattern_name, "error": str(e)}, {}
    except Exception as e:
        if not retry:
            print(f"  {pattern_name}: API error, retrying...")
            time.sleep(5)
            return call_haiku(prompt, pattern_name, retry=True)
        else:
            print(f"  {pattern_name}: FAILED: {e}")
            return {"pattern": pattern_name, "error": str(e)}, {}


def main():
    all_interviews = []
    total_in = 0
    total_out = 0

    for pattern_name, items in sorted(interview_patterns.items(), key=lambda x: -len(x[1])):
        print(f"Interviewing: {pattern_name} ({len(items)} items)...", end=" ", flush=True)
        prompt = build_interview_prompt(pattern_name, items)
        result, usage = call_haiku(prompt, pattern_name)
        total_in += usage.get("prompt_tokens", 0)
        total_out += usage.get("completion_tokens", 0)
        all_interviews.append(result)
        print("OK")
        time.sleep(1)

    output = {
        "timestamp": "2026-03-23",
        "patterns_interviewed": len(all_interviews),
        "total_failures_covered": sum(len(interview_patterns[r["pattern"]]) for r in all_interviews if r.get("pattern") in interview_patterns),
        "interviews": all_interviews,
        "token_usage": {
            "total_input": total_in,
            "total_output": total_out
        }
    }

    out_file = OUTPUT_DIR / "interview_responses.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(all_interviews)} interviews to: {out_file}")
    print(f"Tokens: {total_in} in + {total_out} out")

    # Print summary of suggested rules
    print("\n=== SUGGESTED DETERMINISTIC RULES ===")
    for interview in all_interviews:
        pattern = interview.get("pattern", "?")
        rules = interview.get("deterministic_rules", [])
        if rules:
            print(f"\n{pattern}:")
            for rule in rules:
                print(f"  {rule.get('condition', '?')} => Row {rule.get('cma_row', '?')}")

    print("\n=== SUGGESTED PROMPT ADDITIONS ===")
    for interview in all_interviews:
        pattern = interview.get("pattern", "?")
        additions = interview.get("suggested_prompt_additions", [])
        if additions:
            print(f"\n{pattern}:")
            for a in additions:
                print(f"  + {a}")


if __name__ == "__main__":
    main()
