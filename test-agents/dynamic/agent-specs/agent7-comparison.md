# Agent 7: Three-Way Comparison & Final Report Assembly

## Your Job
Read all previous agent outputs, perform the three-way accuracy comparison, identify key insights, and assemble the final `DYNAMIC_TEST_REPORT.md`. You are the last agent — your output is what the user reads.

## Inputs (read all these files)
- `test-results/dynamic/dynamic_ground_truth.md` — Claude's independent scan of FY22, FY23, FY25 docs
- `test-results/dynamic/dynamic_cma_known_values.json` — Known correct values from existing CMA
- `test-results/dynamic/dynamic_cma_analysis.md` — CMA analysis report
- `test-results/dynamic/agent1-health.json`
- `test-results/dynamic/agent2-manifest.json`
- `test-results/dynamic/agent3-extraction.md`
- `test-results/dynamic/agent4-classification.md`
- `test-results/dynamic/agent5-excel.md`
- `test-results/dynamic/agent6-e2e.md`

## The Three-Way Comparison

### Comparison 1: Extraction Accuracy (FY22, FY23, FY25 only)
**Question:** How accurately does the app extract financial figures compared to what's actually in the documents?

**Method:**
```python
import json, re

# Load ground truth from pre-scan
with open(r"test-results\dynamic\dynamic_ground_truth.md") as f:
    ground_truth_text = f.read()

# Parse ground truth tables to get {description: amount} dicts per year
# (Parse the markdown tables in dynamic_ground_truth.md)

# Load app's extracted items from Agent 3
# (Parse agent3-extraction.md or fetch from API if needed)

# Match by description (fuzzy) + amount within 1%
# Score: matched_items / total_ground_truth_items × 100

def fuzzy_match(desc1, desc2):
    """Basic fuzzy match — normalize and compare."""
    d1 = re.sub(r'[^a-z0-9 ]', '', desc1.lower().strip())
    d2 = re.sub(r'[^a-z0-9 ]', '', desc2.lower().strip())
    return d1 == d2 or d1 in d2 or d2 in d1

def amount_match(a1, a2, tolerance=0.01):
    if a2 == 0:
        return a1 == 0
    return abs(a1 - a2) / abs(a2) < tolerance
```

**Note on FY24:** The app used Vision OCR to extract FY24 data from a scanned PDF. We cannot compare this against the pre-scan ground truth (which couldn't read the scanned PDF). Instead, FY24 accuracy is measured in Comparison 2 (against the known CMA values).

Expected results:
- FY22 (Excel source): should be very high, 90%+
- FY23 (text PDFs): should be high, 80%+
- FY25 (Excel source): should be very high, 90%+
- FY24 (Vision OCR vs CMA known values): see Comparison 2

### Comparison 2: Classification Accuracy
**Question:** Do the classified CMA rows match the known correct values?

Read from `agent4-classification.md` and `dynamic_cma_known_values.json`:

```python
import json

with open(r"test-results\dynamic\dynamic_cma_known_values.json") as f:
    known = json.load(f)

# From agent4-classification.md, get the row-by-row comparison table
# Calculate: matched_rows / total_key_rows per year

# Key insight: compare manufacturing rows specifically
# R45 (Factory Wages), R48 (Power), R56 (Depreciation) are the differentiators
# from Mehta Computers (which had near-zero values there)
```

### Comparison 3: End-to-End Accuracy
**Question:** Does the final generated CMA file match the human-prepared CMA?

Read from `agent5-excel.md` — the row-by-row comparison was already done there. Summarize it here.

## Delta Analysis: Dynamic vs Mehta

Compare this test's results against Mehta Computers test results:

| Metric | Mehta Computers | Dynamic Air Eng | Notes |
|--------|----------------|-----------------|-------|
| Total items extracted | 162 | ? | |
| FY audited PDFs (scanned) | 0 | ? | Phase 10 test |
| Tier 1 % | 0% | ? | |
| Tier 2 % | 34% | ? | |
| Tier 3 (doubt) % | 66% | ? | Manufacturing = higher expected |
| Key row match % | 100% (10/10) | ? | |
| E2E step 8 (generate) | ❌ FAILED | ? | Fixed? |
| E2E step 9 (download) | ❌ FAILED | ? | Fixed? |

## Industry Insights
Manufacturing vs Trading — note what's different in classification:
- Manufacturing has factory wages, power, raw materials (Mehta had none of these)
- Manufacturing Notes to Accounts are more complex (sub-breakdowns crucial)
- Vision OCR for manufacturing audited statements — quality observations

## Output File
Write the final report to `test-results/dynamic/DYNAMIC_TEST_REPORT.md`:

```markdown
# CMA Automation V1 — Dynamic Air Engineering Test Report

**Generated:** 2026-03-19
**Company:** Dynamic Air Engineering
**Industry:** Manufacturing / Engineering
**Documents tested:** 7 (FY22-FY25), including 1 scanned PDF (33 pages, FY24)
**Test type:** Full pipeline + three-way accuracy comparison

---

## Overall Score: N/8 agents PASS or PARTIAL PASS

| Agent | Purpose | Result | Key Metric |
|-------|---------|--------|------------|
| P1 | Document Scanner | ✅/❌ | N items found across FY22/23/25 |
| P2 | CMA Analyzer | ✅/❌ | N key rows extracted from existing CMA |
| 1 | Infrastructure | ✅/❌ | All N checks green |
| 2 | Document Intelligence | ✅/❌ | FY24 confirmed scanned |
| 3 | Extraction Pipeline | ✅/⚠️/❌ | N total items; FY24 Vision OCR: N items |
| 4 | Classification Quality | ✅/⚠️/❌ | N% accuracy on key rows |
| 5 | Excel Validation | ✅/⚠️/❌ | N% rows match within 1% |
| 6 | E2E Critical Path | ✅/⚠️/❌ | Steps 8+9: FIXED/BROKEN |
| 7 | Three-Way Comparison | ✅ | (this agent) |

---

## Phase 10 Validation: Claude Vision OCR

### FY24 Scanned PDF (33 pages) Results
- Extractor used: OcrExtractor ✅
- Items extracted: N (target: >50)
- Batches sent to Claude Vision: N (15 pages/batch)
- Ambiguity questions flagged: N items
- Sample items extracted: [list 5]

### Vision OCR Quality Assessment
- Amount accuracy vs known CMA values: N%
- Scale detection (in_lakhs / in_crores / absolute): [what was detected]
- Observation: [any interesting patterns, errors, or quality notes]

---

## Three-Way Accuracy Comparison

### Comparison 1: Extraction Accuracy (Text Documents)
| Year | Source Type | Ground Truth Items | App Extracted | Matched | Accuracy |
|------|------------|-------------------|---------------|---------|---------|
| FY22 | Excel + PDFs | N | N | N | N% |
| FY23 | PDFs | N | N | N | N% |
| FY25 | Excel | N | N | N | N% |

### Comparison 2: Classification Accuracy (Key CMA Rows)
| Row | Field | FY22 Known | FY22 App | FY23 Known | FY23 App | FY24 Known | FY24 App |
|-----|-------|-----------|---------|-----------|---------|-----------|---------|
| R22 | Domestic Sales | N | N | N | N | N | N |
| R42 | Raw Materials | N | N | N | N | N | N |
| R45 | Factory Wages | N | N | N | N | N | N |
| R48 | Power/Fuel | N | N | N | N | N | N |
| R56 | Depreciation | N | N | N | N | N | N |
| R67 | Salary | N | N | N | N | N | N |
| R83 | Interest TL | N | N | N | N | N | N |

**Classification Accuracy: N/7 rows matched = N%**

### Comparison 3: End-to-End (Generated CMA vs Existing CMA)
[Summary from Agent 5]

---

## Manufacturing Classification Analysis

### New Rules Generated
[Rules from Agent 4 in RULE X-NNN format]

### Manufacturing vs Trading Differences
- Factory Wages (R45): [populated? correct amount?]
- Power & Fuel (R48): [populated? correct amount?]
- Depreciation on P&M (R56): [populated? correct amount?]
- Notes to Accounts: [were sub-breakdowns extracted correctly?]

---

## E2E Fixes Confirmed (from Mehta Failures)
- File upload (react-dropzone): FIXED ✅ / STILL BROKEN ❌
- Generate CMA button: FIXED ✅ / STILL BROKEN ❌
- Download CMA file: FIXED ✅ / STILL BROKEN ❌

---

## Issues Found

### Critical (must fix before production)
[Any FAIL results]

### Warnings (should fix)
[Any WARNING results]

### Observations (informational)
[Any interesting findings]

---

## Recommendations

### Immediate Actions
1. [Action 1]
2. [Action 2]

### Classification Improvement Rules to Add
[Paste rules from Agent 4]

### For Next Test
1. [What to test next]
```

## Gate Condition
No gate — this is the final agent. Write the report regardless of results.
Include all PASS, WARNING, and FAIL statuses honestly.
