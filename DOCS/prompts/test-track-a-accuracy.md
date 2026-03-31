# Test Track A — Accuracy Benchmark (BCIPL 448 Items)

## Your Role
You are a testing agent. Your ONLY job is to measure the accuracy of the new scoped classification engine against the BCIPL ground truth holdout set. You produce numbers and a report. You do NOT fix bugs or modify the classifier.

## Load Required Skill
Use `superpowers:verification-before-completion` skill before claiming any results.

## Important Notes (Post-Integration Fixes)

> **Model change:** DeepSeek R1 has been replaced with **DeepSeek V3** (`deepseek/deepseek-chat`). R1 was a reasoning model that took ~4 hours per document. V3 is a fast generation model (~1.9s per item).
>
> **Row offset fixed:** `CMA_Ground_Truth_v1/reference/canonical_labels.json` had all `sheet_row` values off by -1. They have been bumped +1 to match the CMA Excel template. Ground truth and canonical_labels now align correctly.
>
> **`classify()` is ASYNC:** The classify method is `async def classify(...)`. You must use `asyncio.run()` or an async test runner. There is also a sync wrapper `classify_sync()` you can call directly if preferred.
>
> **classify signature:**
> ```python
> async def classify(self, raw_text, amount, section, industry_type, document_type, fuzzy_candidates) -> AIClassificationResult
> ```
> Sync wrapper: `classify_sync(self, raw_text, amount, section, industry_type, document_type, fuzzy_candidates) -> AIClassificationResult`
>
> **Ground truth file location:** The BCIPL ground truth file is at **host path** `DOCS/extractions/BCIPL_classification_ground_truth.json`. Inside the Docker worker container, the backend is mounted at `/app` (from `./backend:/app`), so this file is NOT at `/app/DOCS/`. The `CMA_Ground_Truth_v1` directory IS mounted at `/app/CMA_Ground_Truth_v1/`. To use the ground truth file inside Docker, either copy it into the container or add a volume mount for it.

## Pre-Flight Checks (do these FIRST)

### 1. Verify Docker is running
```bash
docker compose ps
```
All 4 services (backend, frontend, worker, redis) must be "Up". If not, run:
```bash
docker compose up -d
```
Wait for all services to start.

### 2. Verify scoped classifier exists and loads
```bash
docker compose exec worker python -c "
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
print('Sections loaded:', len(sc._contexts) if hasattr(sc, '_contexts') else 'unknown')
print('SUCCESS: ScopedClassifier initialized')
"
```
If this fails with ImportError or any error → STOP. The integration is not complete. Report the error and exit.

### 3. Verify OpenRouter connectivity
```bash
docker compose exec worker python -c "
import os
print('OPENROUTER_API_KEY present:', bool(os.environ.get('OPENROUTER_API_KEY')))
from openai import OpenAI
client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.environ.get('OPENROUTER_API_KEY', ''))
try:
    r = client.chat.completions.create(model='deepseek/deepseek-chat', messages=[{'role':'user','content':'Reply with just OK'}], max_tokens=5)
    print('DeepSeek V3:', r.choices[0].message.content.strip())
except Exception as e:
    print('DeepSeek V3 FAILED:', e)
try:
    r2 = client.chat.completions.create(model='google/gemini-2.0-flash-001', messages=[{'role':'user','content':'Reply with just OK'}], max_tokens=5)
    print('Gemini Flash:', r2.choices[0].message.content.strip())
except Exception as e:
    print('Gemini Flash FAILED:', e)
"
```
Both models must respond. If either fails → STOP and report.

### 4. Verify BCIPL test data exists
```bash
docker compose exec worker python -c "
import json, os
# Ground truth file is on the HOST at DOCS/extractions/, NOT inside /app/
# Check if it was copied/mounted into the container
paths_to_try = [
    '/app/DOCS/extractions/BCIPL_classification_ground_truth.json',
    '/app/CMA_Ground_Truth_v1/BCIPL_classification_ground_truth.json',
]
found = False
for p in paths_to_try:
    if os.path.exists(p):
        with open(p) as f:
            data = json.load(f)
        print(f'BCIPL test items: {len(data)} (found at {p})')
        print(f'Sample item keys: {list(data[0].keys())}')
        found = True
        break
if not found:
    print('NOT FOUND inside container. Copy it in first:')
    print('  docker cp DOCS/extractions/BCIPL_classification_ground_truth.json <worker_container>:/app/test_ground_truth.json')
"
```
Expected: 448 items loaded.

---

## The Accuracy Test

### What You're Testing
The scoped classifier routes each line item to a section (23 categories), builds a focused prompt with only that section's CMA rows + rules + examples, then calls DeepSeek V3 and Gemini Flash in parallel for a multi-agent debate. We need to measure how accurate this is vs the 87% baseline.

### Expected Speed & Cost
- **Speed:** ~1.9 seconds per item = ~14 minutes for 448 items (NOT hours — V3 is a fast generation model, not a reasoning model)
- **Cost:** DeepSeek V3 pricing is ~$0.27/$1.10 per 1M input/output tokens. For 448 items with debate, expect roughly $0.50-$2.00 total.

### How To Run It

Create a test script and run it inside the Docker worker container. The script must:

1. Load `BCIPL_classification_ground_truth.json` (448 items)
2. For each item, call the scoped classifier's `classify()` or `classify_sync()` method
3. Compare `predicted_cma_row` with `correct_cma_row` from ground truth
4. Track: correct count, doubt count, error count, per-section accuracy
5. Print running progress every 25 items (with cost if available)
6. Save detailed results to `DOCS/test-results/scoped-v2/`

**IMPORTANT:**
- The scoped classifier is at `app.services.classification.scoped_classifier.ScopedClassifier`
- Find out its exact `classify()` method signature by reading the file first
- The classify method is **async** (uses parallel API calls) — use `asyncio.run()` or call `classify_sync()` instead
- `classify_sync()` is a synchronous wrapper that creates a new event loop internally — safe to call from sync code
- If the method signature differs from what's expected, ADAPT the test script to match
- DO NOT modify the classifier code — only write the test script

### Read the classifier first
```bash
docker compose exec worker cat /app/app/services/classification/scoped_classifier.py | head -100
```
Understand the class, its init, and the classify method signature before writing the test.

### Key paths inside Docker container:
- Classifier: `/app/app/services/classification/scoped_classifier.py`
- Ground truth data: `/app/CMA_Ground_Truth_v1/` (mounted read-only)
- BCIPL test file: **NOT at `/app/DOCS/`** — must be copied in or mounted. Host path is `DOCS/extractions/BCIPL_classification_ground_truth.json`.
- Results output: `/app/DOCS/test-results/scoped-v2/` (create if needed)

### Running the script
You can either:
- Write the script to a temp file and run inside the container
- Or use `docker compose exec worker python -c "..."` for shorter scripts
- Or mount a test script via volume

Choose whatever works. The goal is: get the 448 items classified and accuracy measured.

---

## Metrics To Report

After the test completes, produce this exact table:

```
| Metric                      | Value    | Baseline | Delta    |
|-----------------------------|----------|----------|----------|
| Overall accuracy            | ??%      | 87.0%    | +/-??pp  |
| Doubt rate                  | ??%      | 13.0%    | +/-??pp  |
| Accuracy within classified  | ??%      | —        | —        |
| Errors (wrong, not doubt)   | ??       | —        | —        |
| Agreement rate (both models) | ??%     | —        | —        |
| Debate round triggered      | ?? items | —        | —        |
| Total cost                  | $??.??   | ~$0.50   | —        |
| Time elapsed                | ??s      | —        | —        |
```

Also report:
- **Top 5 worst sections** (lowest accuracy)
- **Top 10 specific errors** (item text, predicted vs correct row)
- **Agreement vs disagreement accuracy** (are agreed items more accurate than debated ones?)

Save all results to `DOCS/test-results/scoped-v2/`:
- `accuracy_results.json` — full detailed results
- `ACCURACY_REPORT.md` — markdown summary

---

## Success Criteria

| Metric | Pass | Acceptable | Fail |
|--------|------|------------|------|
| Overall accuracy | > 90% | > 87% | <= 87% |
| Doubt rate | < 10% | < 13% | >= 15% |
| Accuracy within classified | > 95% | > 90% | < 90% |
| Cost for 448 items | < $2 | < $5 | > $5 |

## Constraints
- DO NOT modify any source code — test only
- DO NOT use OpenRouter for anything other than the classifier's own calls
- DO NOT retry failed items — count them as doubt
- STOP if cost exceeds $5 (something is wrong)
- Save ALL results before reporting
