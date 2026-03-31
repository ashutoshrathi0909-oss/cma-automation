# Accuracy Test Prompts — 9 Companies

Paste each prompt into a separate Claude Code window. All 9 can run in parallel.

**After all 9 finish:** Each will output a file at `test-results/{COMPANY}_wrong_entries.json`. Come back to the main session to combine + deduplicate.

---

## PROMPT 1: BCIPL (224 items, manufacturing)

```
Run a CMA classification accuracy test for BCIPL.

## What to do
1. Create a Python script `test-results/run_accuracy_bcipl.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/BCIPL/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_bcipl.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (may be in crores/lakhs, not rupees — just pass as-is)
- `entry["industry_type"]` = "manufacturing"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (BCIPL has 224, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/BCIPL_accuracy_summary.json`:
```json
{
  "company": "BCIPL",
  "industry": "manufacturing",
  "total_items": 224,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/BCIPL_wrong_entries.json`:
```json
[
  {
    "company": "BCIPL",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "manufacturing",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/BCIPL/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 2: SR_Papers (164 items, trading)

```
Run a CMA classification accuracy test for SR_Papers.

## What to do
1. Create a Python script `test-results/run_accuracy_sr_papers.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/SR_Papers/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_sr_papers.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "trading"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (SR_Papers has 164, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/SR_Papers_accuracy_summary.json`:
```json
{
  "company": "SR_Papers",
  "industry": "trading",
  "total_items": 164,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/SR_Papers_wrong_entries.json`:
```json
[
  {
    "company": "SR_Papers",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "trading",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/SR_Papers/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 3: SSSS (63 items, trading)

```
Run a CMA classification accuracy test for SSSS (Salem Stainless Steel Suppliers).

## What to do
1. Create a Python script `test-results/run_accuracy_ssss.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/SSSS/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_ssss.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "trading"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (SSSS has 63, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/SSSS_accuracy_summary.json`:
```json
{
  "company": "SSSS",
  "industry": "trading",
  "total_items": 63,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/SSSS_wrong_entries.json`:
```json
[
  {
    "company": "SSSS",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "trading",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/SSSS/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 4: INPL (186 items, manufacturing)

```
Run a CMA classification accuracy test for INPL (IFFCO-Nanoventions).

## What to do
1. Create a Python script `test-results/run_accuracy_inpl.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/INPL/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_inpl.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "manufacturing"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (INPL has 186, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/INPL_accuracy_summary.json`:
```json
{
  "company": "INPL",
  "industry": "manufacturing",
  "total_items": 186,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/INPL_wrong_entries.json`:
```json
[
  {
    "company": "INPL",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "manufacturing",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/INPL/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 5: MSL (222 items, manufacturing)

```
Run a CMA classification accuracy test for MSL (Matrix Stampi Limited).

## What to do
1. Create a Python script `test-results/run_accuracy_msl.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/MSL/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_msl.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "manufacturing"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (MSL has 222, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/MSL_accuracy_summary.json`:
```json
{
  "company": "MSL",
  "industry": "manufacturing",
  "total_items": 222,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/MSL_wrong_entries.json`:
```json
[
  {
    "company": "MSL",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "manufacturing",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/MSL/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 6: SLIPL (114 items, manufacturing)

```
Run a CMA classification accuracy test for SLIPL (Suolificio Linea Italia).

## What to do
1. Create a Python script `test-results/run_accuracy_slipl.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/SLIPL/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_slipl.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "manufacturing"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (SLIPL has 114, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/SLIPL_accuracy_summary.json`:
```json
{
  "company": "SLIPL",
  "industry": "manufacturing",
  "total_items": 114,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/SLIPL_wrong_entries.json`:
```json
[
  {
    "company": "SLIPL",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "manufacturing",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/SLIPL/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 7: Kurunji_Retail (49 items, trading)

```
Run a CMA classification accuracy test for Kurunji Retail.

## What to do
1. Create a Python script `test-results/run_accuracy_kurunji.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/Kurunji_Retail/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_kurunji.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "trading"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (Kurunji has 49, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/Kurunji_Retail_accuracy_summary.json`:
```json
{
  "company": "Kurunji_Retail",
  "industry": "trading",
  "total_items": 49,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/Kurunji_Retail_wrong_entries.json`:
```json
[
  {
    "company": "Kurunji_Retail",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "trading",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/Kurunji_Retail/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 8: Dynamic_Air (230 items, manufacturing)

```
Run a CMA classification accuracy test for Dynamic Air Engineering.

## What to do
1. Create a Python script `test-results/run_accuracy_dynamic_air.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/Dynamic_Air/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_dynamic_air.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "manufacturing"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (Dynamic Air has 230, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/Dynamic_Air_accuracy_summary.json`:
```json
{
  "company": "Dynamic_Air",
  "industry": "manufacturing",
  "total_items": 230,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/Dynamic_Air_wrong_entries.json`:
```json
[
  {
    "company": "Dynamic_Air",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "manufacturing",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/Dynamic_Air/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## PROMPT 9: Mehta_Computer (74 items, trading)

```
Run a CMA classification accuracy test for Mehta Computer.

## What to do
1. Create a Python script `test-results/run_accuracy_mehta.py` that:
   - Reads ground truth from `backend/CMA_Ground_Truth_v1/companies/Mehta_Computer/ground_truth_normalized.json`
   - For each item in `database_entries`, calls the ScopedClassifier to classify it
   - Compares predicted `cma_row` vs ground truth `cma_row`
   - Collects all WRONG entries (predicted != correct, including doubts)
   - Saves results

2. Run it inside Docker: `docker compose exec worker python /app/test-results/run_accuracy_mehta.py`

## Script requirements

Reference `backend/run_bcipl_full.py` for the pattern — adapt it for the normalized format.

Key field mapping from ground_truth_normalized.json:
- `entry["cma_row"]` = correct CMA row
- `entry["raw_text"]` = item text to classify
- `entry["section"]` = section header
- `entry["amount"]` = amount (pass as-is)
- `entry["industry_type"]` = "trading"
- `entry["cma_field_name"]` = correct field name

Classifier call pattern:
```python
from app.services.classification.scoped_classifier import ScopedClassifier
sc = ScopedClassifier()
result = sc.classify_sync(
    raw_text=entry["raw_text"],
    amount=entry.get("amount"),
    section=entry.get("section", ""),
    industry_type=entry["industry_type"],
    document_type="profit_and_loss",  # use "balance_sheet" if cma_row >= 111
    fuzzy_candidates=[],
)
```

Document type logic: if `entry["cma_row"] >= 111` use `"balance_sheet"`, else `"profit_and_loss"`.

## Cost guards
- MAX 500 items (Mehta has 74, well under)
- Reinitialize classifier if tokens > 450,000
- Print progress every 25 items

## Output format
Save TWO files:

1. `test-results/Mehta_Computer_accuracy_summary.json`:
```json
{
  "company": "Mehta_Computer",
  "industry": "trading",
  "total_items": 74,
  "correct": <n>,
  "wrong": <n>,
  "doubts": <n>,
  "accuracy_pct": <float>,
  "elapsed_seconds": <float>
}
```

2. `test-results/Mehta_Computer_wrong_entries.json`:
```json
[
  {
    "company": "Mehta_Computer",
    "raw_text": "...",
    "section": "...",
    "amount": ...,
    "correct_cma_row": ...,
    "correct_cma_field": "...",
    "predicted_cma_row": ...,
    "predicted_cma_field": "...",
    "confidence": ...,
    "is_doubt": true/false,
    "doubt_reason": "..." or null,
    "classification_method": "...",
    "industry_type": "trading",
    "document_type": "..."
  }
]
```

## IMPORTANT
- Do NOT run Phase 3 (model interrogation). Only Phase 1 (classify + compare).
- Do NOT modify any source code. Only create the test script and run it.
- Print a final summary table at the end.
- The script runs INSIDE Docker — file paths start with /app/ (e.g., /app/CMA_Ground_Truth_v1/companies/Mehta_Computer/ground_truth_normalized.json)
- Output files go to /app/test-results/ which maps to test-results/ on host.
- If test-results/ directory doesn't exist, create it.
- NEVER use OpenRouter for anything other than the ScopedClassifier calls (no interrogation, no extra experiments).
```

---

## AFTER ALL 9 COMPLETE — Combine Prompt

Paste this into the MAIN session after all 9 are done:

```
All 9 accuracy tests are complete. The results are in test-results/:
- BCIPL_wrong_entries.json, BCIPL_accuracy_summary.json
- SR_Papers_wrong_entries.json, SR_Papers_accuracy_summary.json
- SSSS_wrong_entries.json, SSSS_accuracy_summary.json
- INPL_wrong_entries.json, INPL_accuracy_summary.json
- MSL_wrong_entries.json, MSL_accuracy_summary.json
- SLIPL_wrong_entries.json, SLIPL_accuracy_summary.json
- Kurunji_Retail_wrong_entries.json, Kurunji_Retail_accuracy_summary.json
- Dynamic_Air_wrong_entries.json, Dynamic_Air_accuracy_summary.json
- Mehta_Computer_wrong_entries.json, Mehta_Computer_accuracy_summary.json

Do the following:

1. Load all 9 summary files and print a combined accuracy table (company, items, correct, wrong, doubts, accuracy%)

2. Load all 9 wrong_entries files and combine into one list

3. Deduplicate by (raw_text_normalized, correct_cma_row, predicted_cma_row) — where raw_text_normalized is lowercase, stripped of extra spaces. Keep ALL company names that share a duplicate (comma-separated).

4. Sort deduplicated entries by correct_cma_row (ascending)

5. Save:
   - `test-results/COMBINED_wrong_entries.json` — full deduplicated list
   - `test-results/COMBINED_accuracy_summary.json` — overall stats
   - `test-results/CA_REVIEW_SHEET.md` — markdown table for CA review with columns:
     | # | Item Text | Section | Correct Row (GT) | Correct Field (GT) | Model Predicted Row | Model Predicted Field | Companies | CA Decision |
     The "CA Decision" column should be blank — for the CA to fill in.

6. Print summary: total wrong across all companies, unique wrong after dedup, top 10 most common wrong predictions (by predicted_cma_row).
```
