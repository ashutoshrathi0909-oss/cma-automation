# Scoped Classification v2 — Testing Plan

> **For agentic workers:** This is a TESTING plan, not a feature build. Use multi-agent execution: dispatch parallel agents for independent test tracks. DO NOT use OpenRouter for any testing — use Agent(model="haiku") if LLM calls are needed for test setup.

**Goal:** Validate that the scoped classification + multi-agent debate (DeepSeek R1 + Gemini Flash) integration works correctly and improves accuracy beyond the 87% baseline.

**Architecture:** Two parallel test tracks — Track A (accuracy benchmark on BCIPL 448-item holdout) and Track B (full app E2E through browser). Track A proves the classifier works. Track B proves the integration works.

**Prerequisites:** Sonnet has completed the backend integration from `DOCS/prompts/scoped-classification-v2-prompt.md`. Docker builds and starts clean.

---

## Pre-Flight Checks

- [ ] **Step 1: Verify Docker builds**

```bash
docker compose build
```
Expected: All 4 services build without errors.

- [ ] **Step 2: Start all services**

```bash
docker compose up -d
```
Expected: backend, frontend, worker, redis all start. Check logs:
```bash
docker compose logs worker --tail=20
```
Expected: Worker starts, scoped classifier loads ground truth data (look for log lines about loading canonical labels, rules, training examples).

- [ ] **Step 3: Verify scoped classifier initialization**

```bash
docker compose logs worker 2>&1 | grep -i "scoped\|ground.truth\|canonical\|section.*loaded"
```
Expected: Log lines confirming ground truth data was loaded. If not found, the integration has a bug — stop and fix before proceeding.

- [ ] **Step 4: Verify OpenRouter connectivity**

```bash
docker compose exec backend python -c "
import os
from openai import OpenAI
client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.environ['OPENROUTER_API_KEY'])
r = client.chat.completions.create(model='deepseek/deepseek-r1', messages=[{'role':'user','content':'Say OK'}], max_tokens=10)
print('DeepSeek R1:', r.choices[0].message.content)
r2 = client.chat.completions.create(model='google/gemini-2.0-flash-001', messages=[{'role':'user','content':'Say OK'}], max_tokens=10)
print('Gemini Flash:', r2.choices[0].message.content)
"
```
Expected: Both models respond. If either fails, check OPENROUTER_API_KEY in .env and model IDs.

---

## Track A: Accuracy Benchmark (BCIPL 448 Items)

**Purpose:** Measure exact classification accuracy against ground truth. This runs the scoped classifier directly (not through the web app) to isolate classification quality from extraction/UI issues.

**Test set:** `DOCS/extractions/BCIPL_classification_ground_truth.json` (448 items, holdout — NOT used in training examples)

- [ ] **Step 5: Create accuracy test script**

Create `tests/test_scoped_accuracy.py`:

```python
"""
Accuracy benchmark: run BCIPL 448 items through the scoped classifier.
Compares predicted cma_row vs ground truth correct_cma_row.
Outputs detailed metrics to DOCS/test-results/scoped-v2/
"""
import json
import sys
import time
from pathlib import Path

# Add backend to path so we can import the service
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.classification.scoped_classifier import ScopedClassifier

BASE = Path(__file__).parent.parent
BCIPL_PATH = BASE / "DOCS" / "extractions" / "BCIPL_classification_ground_truth.json"
RESULTS_DIR = BASE / "DOCS" / "test-results" / "scoped-v2"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_accuracy_test():
    # Load test data
    with open(BCIPL_PATH, encoding="utf-8") as f:
        test_items = json.load(f)
    print(f"Loaded {len(test_items)} BCIPL test items")

    # Initialize classifier
    classifier = ScopedClassifier()
    print("Scoped classifier initialized")

    results = []
    correct = 0
    doubt = 0
    errors = 0
    start = time.time()

    for i, item in enumerate(test_items):
        try:
            result = classifier.classify(
                raw_text=item["raw_text"],
                section=item.get("section", ""),
                sheet_name=item.get("sheet_name", ""),
                industry_type="manufacturing",
                document_type="profit_and_loss",  # or derive from sheet
                amount=item.get("amount_rupees"),
            )

            predicted_row = result.get("cma_row", 0)
            correct_row = item["correct_cma_row"]
            is_correct = (predicted_row == correct_row)
            is_doubt = result.get("is_doubt", False)

            if is_correct:
                correct += 1
            if is_doubt:
                doubt += 1
            if not is_correct and not is_doubt:
                errors += 1

            results.append({
                "index": i,
                "raw_text": item["raw_text"],
                "sheet_name": item.get("sheet_name", ""),
                "section": item.get("section", ""),
                "correct_cma_row": correct_row,
                "predicted_cma_row": predicted_row,
                "is_correct": is_correct,
                "is_doubt": is_doubt,
                "confidence": result.get("confidence_score", 0),
                "method": result.get("classification_method", ""),
                "reasoning": result.get("reasoning", ""),
            })

            if (i + 1) % 25 == 0:
                elapsed = time.time() - start
                acc = correct / (i + 1)
                print(f"  [{i+1}/{len(test_items)}] acc={acc:.1%} doubt={doubt} errors={errors} ({elapsed:.0f}s)")

        except Exception as e:
            print(f"  ERROR on item {i}: {e}")
            results.append({
                "index": i,
                "raw_text": item["raw_text"],
                "correct_cma_row": item["correct_cma_row"],
                "predicted_cma_row": 0,
                "is_correct": False,
                "is_doubt": True,
                "error": str(e),
            })
            doubt += 1

    # Final metrics
    total = len(test_items)
    classified = total - doubt
    correct_classified = sum(1 for r in results if r["is_correct"] and not r.get("is_doubt"))
    elapsed = time.time() - start

    metrics = {
        "total": total,
        "correct": correct,
        "doubt": doubt,
        "errors": errors,
        "classified": classified,
        "correct_within_classified": correct_classified,
        "overall_accuracy": round(correct / total, 4),
        "doubt_rate": round(doubt / total, 4),
        "accuracy_within_classified": round(correct_classified / classified, 4) if classified > 0 else 0,
        "elapsed_seconds": round(elapsed, 1),
        "baseline": 0.87,
    }

    # Print report
    print(f"\n{'='*60}")
    print(f"SCOPED CLASSIFICATION v2 — ACCURACY REPORT")
    print(f"{'='*60}")
    print(f"Total items:              {total}")
    print(f"Correct:                  {correct} ({metrics['overall_accuracy']:.1%})")
    print(f"Doubt:                    {doubt} ({metrics['doubt_rate']:.1%})")
    print(f"Errors (wrong, not doubt):{errors}")
    print(f"Classified (non-doubt):   {classified}")
    print(f"Correct within classified:{correct_classified} ({metrics['accuracy_within_classified']:.1%})")
    print(f"Time:                     {elapsed:.0f}s")
    print(f"Baseline:                 87.0%")
    print(f"Delta:                    {(metrics['overall_accuracy'] - 0.87)*100:+.1f}pp")
    print(f"{'='*60}")

    # Save
    with open(RESULTS_DIR / "accuracy_results.json", "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "items": results}, f, indent=2, ensure_ascii=False)
    print(f"Saved to {RESULTS_DIR / 'accuracy_results.json'}")

    # Save markdown
    verdict = "BEATS BASELINE" if metrics["overall_accuracy"] > 0.87 else "BELOW BASELINE"
    md = f"""# Scoped Classification v2 — Accuracy Results

**Verdict: {verdict}**

| Metric | Value | Baseline |
|--------|-------|----------|
| Overall accuracy | {metrics['overall_accuracy']:.1%} | 87.0% |
| Doubt rate | {metrics['doubt_rate']:.1%} | 13.0% |
| Accuracy within classified | {metrics['accuracy_within_classified']:.1%} | — |
| Errors (wrong, not doubt) | {errors} | — |
| Time | {elapsed:.0f}s | — |
| Delta vs baseline | {(metrics['overall_accuracy'] - 0.87)*100:+.1f}pp | — |
"""
    with open(RESULTS_DIR / "ACCURACY_REPORT.md", "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Saved to {RESULTS_DIR / 'ACCURACY_REPORT.md'}")


if __name__ == "__main__":
    run_accuracy_test()
```

- [ ] **Step 6: Run accuracy test inside Docker**

```bash
docker compose exec worker python /app/../tests/test_scoped_accuracy.py
```

Or if the test script is mounted at project root:
```bash
docker compose exec backend python -c "exec(open('/app/tests/test_scoped_accuracy.py').read())"
```

Adjust the command based on where the script is accessible inside the container. The key requirement: the script must be able to import `app.services.classification.scoped_classifier` and access the ground truth files.

Expected output: Accuracy report printed to console + saved to `DOCS/test-results/scoped-v2/`.

- [ ] **Step 7: Evaluate results**

**Success criteria for Track A:**
| Metric | Target | Acceptable | Fail |
|--------|--------|------------|------|
| Overall accuracy | > 90% | > 87% (beats baseline) | <= 87% |
| Doubt rate | < 10% | < 13% (beats baseline) | >= 13% |
| Accuracy within classified | > 95% | > 90% | < 90% |
| Total cost (448 items) | < $2.00 | < $5.00 | > $5.00 |

If FAIL: stop, analyze error patterns, report back before proceeding to Track B.

---

## Track B: Full App E2E Test (Browser)

**Purpose:** Validate the complete workflow works end-to-end through the web UI with the new scoped classifier active.

**Test document:** Use a BCIPL financial statement PDF or Excel from `DOCS/Financials/` (whichever is easiest to upload).

- [ ] **Step 8: Open the app in browser**

Navigate to `http://localhost:3002`
Expected: Login page loads.

- [ ] **Step 9: Login**

Use the dev credentials (check .env for admin email/password or use the dev bypass if configured).
Expected: Dashboard loads.

- [ ] **Step 10: Create a test client**

Go to Clients → New Client:
- Name: "Scoped v2 Test"
- Industry: Manufacturing
- Save

Expected: Client detail page loads.

- [ ] **Step 11: Upload a document**

Upload one of the BCIPL financial documents from `DOCS/Financials/BCIPL/`.
Select document type (P&L or Balance Sheet).
Expected: Upload succeeds, extraction starts automatically or can be triggered.

- [ ] **Step 12: Wait for extraction + verify**

Wait for extraction to complete (check status on the page).
Go to the Verify page → review extracted line items.
Mark as Verified.
Expected: Extraction status changes to "verified".

- [ ] **Step 13: Trigger classification**

After verification, classification should start automatically (or trigger via button).
Expected: Worker logs show:
```
run_classification started for document_id=...
```
And scoped classifier logs showing:
- Section routing for each item
- DeepSeek R1 + Gemini Flash calls
- Agreement/debate decisions
- Cost tracking

- [ ] **Step 14: Check worker logs for debate protocol**

```bash
docker compose logs worker --tail=100
```

Look for:
- "AGREE" messages (both models agreed → auto-approve)
- "DISAGREE → debate" messages (models disagreed → debate round)
- "DOUBT" messages (persistent disagreement → flagged)
- Cost summary at end

Expected: Mix of agreements and debates. Doubt rate should be < 15%.

- [ ] **Step 15: Review classifications in browser**

Go to the CMA report → Review page.
Expected:
- Classified items show with confidence scores
- Doubt items appear in the doubt report
- Classification method shows "scoped_debate" or similar (not "ai_haiku")

- [ ] **Step 16: Check doubt report**

Go to the Doubts page.
Expected: Doubt items listed with reasoning from both models. Should be < 15% of total items.

- [ ] **Step 17: Generate Excel**

Approve/resolve enough items to enable Excel generation.
Trigger Excel generation.
Expected: .xlsm file downloads, opens in Excel with data filled in.

- [ ] **Step 18: Verify Excel correctness**

Open the downloaded .xlsm:
- VBA macros preserved (file is .xlsm, not .xlsx)
- Data appears in INPUT SHEET
- TL Sheet populated by macros
- Spot-check 5-10 values against the source document

---

## Post-Test Analysis

- [ ] **Step 19: Compile results**

Create a summary comparing:
| Metric | Old Pipeline (87% baseline) | Scoped v2 (Track A) | Full App (Track B) |
|--------|----------------------------|---------------------|-------------------|
| Accuracy | 87% | [from Step 7] | [spot-check] |
| Doubt rate | 13% | [from Step 7] | [from Step 16] |
| Cost per doc | ~$0.10 (Haiku) | [from logs] | [from logs] |
| Time per doc | ? | [from Step 6] | [from Step 13-17] |

- [ ] **Step 20: Decision point**

Based on results:
- **If accuracy > 90%:** Proceed to production hardening
- **If accuracy 87-90%:** Analyze errors, tune section routing/prompts, re-test
- **If accuracy < 87%:** Scoped approach failed, debug why, consider alternatives

---

## Agent Execution Strategy

This plan should be executed with **two parallel agents** after pre-flight checks pass:

**Agent 1 (Track A):** Run the accuracy benchmark script. This is the critical path — gives us hard numbers.

**Agent 2 (Track B):** Run the browser E2E test. This validates integration but doesn't give accuracy numbers.

Pre-flight checks (Steps 1-4) must complete BEFORE dispatching parallel agents.

**Model for execution:** Sonnet (coding/execution work, not planning)

---

*Created 2026-03-26. Tests the scoped classification + multi-agent debate integration.*
