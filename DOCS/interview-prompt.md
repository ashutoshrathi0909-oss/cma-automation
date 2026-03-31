# Model Interview Prompt — Genuinely Wrong Items

Paste this into a Claude Code window AFTER accuracy tests for all companies are complete.

**What it does:** Reads all wrong_entries files, filters out the +1 GT offset bug, identifies genuinely wrong items, then interviews DeepSeek V3 about each one to understand WHY it picked the wrong row.

**Estimated cost:** ~$0.15-0.30 on OpenRouter (~201 unique genuinely wrong items, capped at 100 interviews)

---

## PROMPT (copy everything below)

```
## Task: Interview DeepSeek V3 about misclassified CMA items

There is a systematic row offset bug in the ground truth files — the normalized GT uses row N-1 while the classifier correctly uses row N. BUT the filter is smarter: compare by FIELD NAME, not row offset. If the predicted field name matches the correct field name, it's a GT numbering bug (not a real error). Only interview items where the field names DIFFER.

**Known numbers:** 1,163 total wrong → 864 GT offset bugs → 299 genuinely wrong → ~201 unique after dedup.

### Step 1: Create the interview script

Create `backend/test-results/run_interview.py` that runs inside Docker:
`docker compose exec worker python /app/test-results/run_interview.py`

The script should:

#### 1A. Load all wrong entries files
```python
import json, glob, os, time
from pathlib import Path

RESULTS_DIR = Path("/app/test-results")
wrong_files = sorted(RESULTS_DIR.glob("*_wrong_entries.json"))
all_wrong = []
for f in wrong_files:
    with open(f, encoding="utf-8") as fh:
        entries = json.load(fh)
        all_wrong.extend(entries)
print(f"Loaded {len(all_wrong)} wrong entries from {len(wrong_files)} files")
```

#### 1B. Filter out GT offset items (same field name = not real errors)
IMPORTANT: BCIPL's session compared by cma_code (correct rows already in classifier scheme).
Other companies have GT rows off by -1. Use FIELD NAME matching as the filter — it works for both.

```python
genuinely_wrong = []
offset_bug = []
for item in all_wrong:
    correct_field = (item.get("correct_cma_field") or "").strip().lower()
    predicted_field = (item.get("predicted_cma_field") or "").strip().lower()

    if item.get("is_doubt"):
        genuinely_wrong.append(item)
    elif correct_field and predicted_field and correct_field == predicted_field:
        # Same field name, different row number = GT numbering bug
        offset_bug.append(item)
    else:
        genuinely_wrong.append(item)

print(f"GT offset bug (same field name): {len(offset_bug)}")
print(f"Genuinely wrong (diff field):    {len(genuinely_wrong)}")
```

#### 1C. Deduplicate by (raw_text_lower, correct_field, predicted_field)
```python
seen = set()
unique_wrong = []
for item in genuinely_wrong:
    key = (
        item["raw_text"].strip().lower(),
        (item.get("correct_cma_field") or "").lower(),
        (item.get("predicted_cma_field") or "").lower(),
    )
    if key not in seen:
        seen.add(key)
        unique_wrong.append(item)

print(f"Unique genuinely wrong: {len(unique_wrong)}")
```

#### 1D. Interview DeepSeek V3 about each unique wrong item

For each item, rebuild the classifier's context and ask V3 why it chose wrong.

```python
from app.services.classification.scoped_classifier import ScopedClassifier
from openai import OpenAI
import os

sc = ScopedClassifier()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# COST GUARD: max 100 interview calls
MAX_INTERVIEWS = 100
interview_results = []
api_calls = 0

for i, item in enumerate(unique_wrong[:MAX_INTERVIEWS]):
    raw_text = item["raw_text"]
    section = item.get("section", "")
    amount = item.get("amount")
    predicted_row = item.get("predicted_cma_row")
    doc_type = item.get("document_type", "profit_and_loss")

    # BCIPL already has correct rows (compared by cma_code); others need +1
    correct_row_raw = item["correct_cma_row"]
    if item.get("company") == "BCIPL":
        correct_row = correct_row_raw  # already in classifier scheme
    else:
        correct_row = correct_row_raw + 1  # adjust for GT -1 offset

    # Get field names from classifier's label map
    correct_name = sc._labels_by_row.get(correct_row, {}).get("name", f"Row {correct_row}")
    predicted_name = (
        sc._labels_by_row.get(predicted_row, {}).get("name", f"Row {predicted_row}")
        if predicted_row else "DOUBT"
    )

    # Rebuild the exact prompt the classifier would have sent
    sections = sc._route_section(raw_text, section or "", doc_type)
    if len(sections) == 1:
        context = sc._contexts.get(sections[0]) or sc._contexts["admin_expense"]
    else:
        context = sc._merge_contexts(sections)
    original_prompt = sc._build_prompt(raw_text, amount, section or "not specified", context)

    # Check if correct row was even in the options
    available_rows = [r["sheet_row"] for r in context.cma_rows]
    correct_in_list = correct_row in available_rows

    # Build interview question — two parts:
    # Part A: Why did you get it wrong?
    # Part B: What would the input need to look like for you to get it RIGHT?
    interview_q = f"""You classified this financial line item:
"{raw_text}" (section: "{section}", amount: {amount})

You chose: Row {predicted_row} ({predicted_name})
The CORRECT answer is: Row {correct_row} ({correct_name})
Was Row {correct_row} in the options you were shown? {"YES" if correct_in_list else "NO — it was NOT in your options"}

Here was the full prompt you received:
---
{original_prompt}
---

Answer ALL of these:

PART A — Why it went wrong:
1. Was Row {correct_row} ({correct_name}) in the POSSIBLE CMA ROWS list? (Yes/No)
2. If yes: why did you pick Row {predicted_row} instead?
3. If no: what keywords in the item text should have triggered routing to the correct section?

PART B — What would make you get it RIGHT:
4. Write the EXACT minimum change to the prompt that would make you confidently pick Row {correct_row}. Examples:
   - "Add Row {correct_row} ({correct_name}) to the POSSIBLE CMA ROWS list"
   - "Add a rule: 'Electric Charges → Row 48 (Power & Fuel)'"
   - "Add an example: 'Electric Charges' → Row {correct_row} ({correct_name})"
   - "Change the routing keyword pattern to include 'electric' → manufacturing_expense"
5. If you had to write ONE routing regex pattern that would correctly route this item, what would it be? Write it in Python regex format.

Be specific and actionable. Max 200 words."""

    try:
        resp = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[{"role": "user", "content": interview_q}],
            max_tokens=250,
            temperature=0.0,
        )
        answer = resp.choices[0].message.content.strip()
        api_calls += 1
    except Exception as e:
        answer = f"ERROR: {e}"

    interview_results.append({
        "index": i,
        "company": item.get("company", "unknown"),
        "raw_text": raw_text,
        "section": section,
        "correct_row_adjusted": correct_row,
        "correct_name": correct_name,
        "predicted_row": predicted_row,
        "predicted_name": predicted_name,
        "correct_row_in_options": correct_in_list,
        "routed_to": sections,
        "model_response": answer,
    })

    status = "IN_LIST" if correct_in_list else "NOT_IN_LIST"
    print(f"[{i+1}/{min(len(unique_wrong), MAX_INTERVIEWS)}] {status} | '{raw_text[:50]}' | correct={correct_row} pred={predicted_row}")

    if api_calls >= MAX_INTERVIEWS:
        print(f"Cost guard: {api_calls} calls reached")
        break
```

#### 1E. Analyze patterns and save results

```python
# Pattern analysis
not_in_list = sum(1 for r in interview_results if not r["correct_row_in_options"])
in_list_wrong = sum(1 for r in interview_results if r["correct_row_in_options"])

print(f"\n{'='*60}")
print(f"INTERVIEW SUMMARY")
print(f"{'='*60}")
print(f"Total interviewed:         {len(interview_results)}")
print(f"Correct row NOT in list:   {not_in_list} ({not_in_list/max(len(interview_results),1)*100:.0f}%) — ROUTING BUG")
print(f"Correct row IN list:       {in_list_wrong} ({in_list_wrong/max(len(interview_results),1)*100:.0f}%) — MODEL ERROR")
print(f"API calls used:            {api_calls}")

# Save full results
output = {
    "summary": {
        "total_wrong_all_companies": len(all_wrong),
        "gt_offset_bug": len(offset_bug),
        "genuinely_wrong": len(genuinely_wrong),
        "unique_genuinely_wrong": len(unique_wrong),
        "interviewed": len(interview_results),
        "correct_not_in_options": not_in_list,
        "correct_in_options_but_wrong": in_list_wrong,
        "api_calls": api_calls,
    },
    "interviews": interview_results,
}

with open(RESULTS_DIR / "INTERVIEW_RESULTS.json", "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Save a CA-friendly markdown report
lines = [
    "# Model Interview Results — Genuinely Wrong Items",
    "",
    f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}",
    f"**Total wrong across all companies:** {len(all_wrong)}",
    f"**GT offset bugs (not real errors):** {len(offset_bug)}",
    f"**Genuinely wrong:** {len(genuinely_wrong)}",
    f"**Unique (deduplicated):** {len(unique_wrong)}",
    f"**Interviewed:** {len(interview_results)}",
    "",
    "## Root Cause Split",
    "",
    f"- **Routing bug** (correct row not in options): {not_in_list} ({not_in_list/max(len(interview_results),1)*100:.0f}%)",
    f"- **Model error** (correct row available, picked wrong): {in_list_wrong} ({in_list_wrong/max(len(interview_results),1)*100:.0f}%)",
    "",
    "## Items Where Correct Row Was NOT In Options (Routing Fix Needed)",
    "",
    "| # | Item | Section | Correct Row | Predicted Row | Companies | Routed To |",
    "|---|------|---------|-------------|---------------|-----------|-----------|",
]

for r in interview_results:
    if not r["correct_row_in_options"]:
        lines.append(
            f"| {r['index']+1} | {r['raw_text'][:40]} | {r['section'][:20]} | "
            f"{r['correct_row_adjusted']} ({r['correct_name']}) | "
            f"{r['predicted_row']} ({r['predicted_name']}) | "
            f"{r['company']} | {','.join(r['routed_to'])} |"
        )

lines += [
    "",
    "## Items Where Model Had The Right Options But Chose Wrong",
    "",
    "| # | Item | Correct | Predicted | V3 Explanation |",
    "|---|------|---------|-----------|----------------|",
]

for r in interview_results:
    if r["correct_row_in_options"]:
        explanation = r["model_response"][:120].replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {r['index']+1} | {r['raw_text'][:35]} | "
            f"R{r['correct_row_adjusted']} ({r['correct_name'][:15]}) | "
            f"R{r['predicted_row']} ({r['predicted_name'][:15]}) | "
            f"{explanation} |"
        )

lines += [
    "",
    "## Suggested Fixes (extracted from V3 responses)",
    "",
    "These are the concrete fixes V3 suggested to make it get the right answer.",
    "Review with CA before implementing.",
    "",
]

# Extract fix suggestions — look for lines containing "Add", "Change", "Route", regex patterns
import re as _re
fix_suggestions = []
for r in interview_results:
    resp = r.get("model_response", "")
    # Extract lines that look like actionable fixes
    for line in resp.split("\n"):
        line = line.strip()
        if any(kw in line.lower() for kw in ["add row", "add a rule", "add an example", "change the routing", "regex", "pattern", "→", "->"]):
            fix_suggestions.append({
                "item": r["raw_text"][:50],
                "correct": f"Row {r['correct_row_adjusted']} ({r['correct_name']})",
                "fix": line,
                "type": "routing" if not r["correct_row_in_options"] else "prompt",
            })

for fs in fix_suggestions:
    lines.append(f"- **{fs['item']}** (correct: {fs['correct']}, type: {fs['type']})")
    lines.append(f"  - {fs['fix']}")
    lines.append("")

if not fix_suggestions:
    lines.append("(No structured fix suggestions extracted — check full responses below)")
    lines.append("")

lines += [
    "",
    "## Full Model Responses",
    "",
]
for r in interview_results:
    lines += [
        f"### {r['index']+1}. `{r['raw_text'][:60]}` ({r['company']})",
        f"- Correct: Row {r['correct_row_adjusted']} ({r['correct_name']})",
        f"- Predicted: Row {r['predicted_row']} ({r['predicted_name']})",
        f"- Correct in options: {'Yes' if r['correct_row_in_options'] else 'NO'}",
        f"- Routed to: {', '.join(r['routed_to'])}",
        "",
        f"**V3 Response:** {r['model_response']}",
        "",
    ]

with open(RESULTS_DIR / "INTERVIEW_REPORT.md", "w") as f:
    f.write("\n".join(lines))

print(f"\nFiles saved:")
print(f"  {RESULTS_DIR / 'INTERVIEW_RESULTS.json'}")
print(f"  {RESULTS_DIR / 'INTERVIEW_REPORT.md'}")
```

### Step 2: Run it
```bash
docker compose exec worker python /app/test-results/run_interview.py
```

### Step 3: Show me the results
After the script completes, show me:
1. The summary (total wrong, GT bugs, genuinely wrong, routing bugs vs model errors)
2. The first 10 items from INTERVIEW_REPORT.md

### CRITICAL RULES
- Filter by FIELD NAME match, not row offset. Same field name = GT numbering bug, not a real error.
- BCIPL wrong entries already have correct row numbering (compared by cma_code). Other companies need +1 adjustment.
- MAX 100 OpenRouter API calls (cost guard)
- Do NOT modify any source code — only create and run the interview script
- The script runs INSIDE Docker (paths start with /app/)
- Output goes to /app/test-results/ (maps to backend/test-results/ on host)
- Print progress for every item
- The interview question asks V3 to suggest the EXACT fix (routing regex, rule, or example) — extract these into the "Suggested Fixes" section of the report
```
