# Agent 3: Extraction Pipeline

## Your Job
Upload all Dynamic Air Engineering financial documents to the app, trigger extraction for each one, verify items, and record exactly how many line items were extracted per document. The FY24 scanned PDF is the primary test of Phase 10 Vision OCR.

## System State
- Backend: http://localhost:8000
- Auth bypass: DISABLE_AUTH=true → pass these headers on every API call:
  `X-User-Id: 00000000-0000-0000-0000-000000000001`
  `X-User-Role: admin`
- Working directory: `C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2`

## Step 1: Create Client

```bash
curl -s -X POST http://localhost:8000/api/clients/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d '{"name": "Dynamic Air Engineering", "industry": "manufacturing", "contact_email": "dynamic@test.com"}' \
  | python -m json.tool
```

Save the returned `id` as `CLIENT_ID`. If client already exists (409 conflict), fetch it:
```bash
curl -s http://localhost:8000/api/clients/ \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  | python -c "import sys,json; clients=json.load(sys.stdin); [print(c['id'], c['name']) for c in clients]"
```

## Step 2: Create CMA Report

```bash
curl -s -X POST http://localhost:8000/api/cma-reports/ \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  -d "{\"client_id\": \"$CLIENT_ID\", \"title\": \"Dynamic Air Engineering CMA FY22-25\", \"base_year\": 2022, \"num_years\": 4}" \
  | python -m json.tool
```

Save the returned `id` as `REPORT_ID`.

## Step 3: Upload and Extract Documents

For EACH document below, perform this 4-step sequence:
1. Upload → get document_id
2. Trigger extraction
3. Poll until complete (or timeout 15 min)
4. Fetch line items + record count

### Upload Function (reuse for all documents)
```python
import requests, json, time

BASE = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "00000000-0000-0000-0000-000000000001",
    "X-User-Role": "admin"
}

def upload_and_extract(file_path, financial_year, doc_type, report_id, timeout_minutes=15):
    # Upload
    with open(file_path, "rb") as f:
        filename = file_path.split("\\")[-1]
        resp = requests.post(f"{BASE}/api/documents/upload",
            headers=HEADERS,
            data={"report_id": report_id, "financial_year": financial_year, "document_type": doc_type},
            files={"file": (filename, f)}
        )
    doc = resp.json()
    doc_id = doc["id"]
    print(f"Uploaded {filename} → doc_id: {doc_id}")

    # Trigger extraction
    resp = requests.post(f"{BASE}/api/documents/{doc_id}/extract", headers=HEADERS)
    print(f"Extraction triggered: {resp.status_code}")

    # Poll
    start = time.time()
    while time.time() - start < timeout_minutes * 60:
        resp = requests.get(f"{BASE}/api/documents/{doc_id}", headers=HEADERS)
        status = resp.json().get("status", "")
        print(f"  Status: {status}")
        if status in ("completed", "failed"):
            break
        time.sleep(10)

    # Fetch items
    resp = requests.get(f"{BASE}/api/documents/{doc_id}/line-items", headers=HEADERS)
    items = resp.json()
    print(f"  Items extracted: {len(items)}")
    return doc_id, status, items
```

### Documents to Process (in this exact order)

#### Document 1: FY22 Balance Sheet (Excel)
```
file: DOCS\Financials\FY_22\Financials\BS-Dynamic 2022 - Companies Act.xlsx
financial_year: 2022
doc_type: audited
target_items: > 20
extractor_expected: ExcelExtractor
```

#### Document 2: FY22 Notes to Accounts (PDF)
```
file: DOCS\Financials\FY_22\Financials\Notes to Financials.pdf
financial_year: 2022
doc_type: notes
target_items: > 15
extractor_expected: PdfExtractor
note: Notes have sub-breakdowns — these are CRITICAL for manufacturing classification
```

#### Document 3: FY22 ITR Balance Sheet & P&L (PDF)
```
file: DOCS\Financials\FY_22\Financials\ITR BS P&L.pdf
financial_year: 2022
doc_type: audited
target_items: > 15
extractor_expected: PdfExtractor
```

#### Document 4: FY23 ITR P&L & Balance Sheet (PDF)
```
file: DOCS\Financials\FY-23\ITR PL & BS.pdf
financial_year: 2023
doc_type: audited
target_items: > 20
extractor_expected: PdfExtractor
```

#### Document 5: FY23 Notes to Accounts (PDF)
```
file: DOCS\Financials\FY-23\Notes..pdf
financial_year: 2023
doc_type: notes
target_items: > 15
extractor_expected: PdfExtractor
```

#### Document 6: FY24 Audited Financials — SCANNED PDF ← PRIMARY TEST
```
file: DOCS\Financials\FY-24\Audited Financials FY-2024 (1).pdf
financial_year: 2024
doc_type: audited
target_items: > 50   ← HARD GATE — if < 50, Vision OCR failed
extractor_expected: OcrExtractor (Claude Vision)
timeout: 15 minutes (3 batches × ~3 min each)
```

After triggering FY24 extraction, immediately run:
```bash
docker compose logs worker --follow --tail=5
```
Watch for these log lines (confirms Vision OCR is running):
```
OcrExtractor
Converted PDF to 33 page images
After blank-page filter: N pages with content
Batch 1-15: extracted N items
Batch 16-30: extracted N items
Vision OCR complete: N total line items
```

If you see `PdfExtractor` instead of `OcrExtractor` — STOP. This means the scanned PDF was not routed correctly. Report to orchestrator.

#### Document 7: FY25 Provisional (Excel)
```
file: DOCS\Financials\FY2025\Provisional financial 31.03.25 (3).xlsx
financial_year: 2025
doc_type: provisional
target_items: > 20
extractor_expected: ExcelExtractor
```

## Step 4: Verify All Items (MANDATORY)

Per CLAUDE.md — verification is mandatory between extraction and classification.

```bash
curl -s -X POST http://localhost:8000/api/cma-reports/$REPORT_ID/verify-all \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"
```

Or verify per document:
```bash
curl -s -X POST http://localhost:8000/api/documents/$DOC_ID/verify \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin"
```

Check for ambiguity_question items (new in Phase 10):
```bash
curl -s http://localhost:8000/api/cma-reports/$REPORT_ID/line-items \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  | python -c "
import sys, json
items = json.load(sys.stdin)
ambiguous = [i for i in items if i.get('ambiguity_question')]
print(f'Total items: {len(items)}')
print(f'Ambiguity questions: {len(ambiguous)}')
for i in ambiguous[:5]:
    print(f'  - {i[\"description\"]}: {i[\"ambiguity_question\"]}')
"
```

## Step 5: FY24 Vision OCR Deep Check

After FY24 extraction completes, fetch its items and verify quality:
```bash
curl -s http://localhost:8000/api/documents/$FY24_DOC_ID/line-items \
  -H "X-User-Id: 00000000-0000-0000-0000-000000000001" \
  -H "X-User-Role: admin" \
  | python -c "
import sys, json
items = json.load(sys.stdin)
sections = {}
for i in items:
    s = i.get('section', 'unknown')
    sections[s] = sections.get(s, 0) + 1
print(f'FY24 Vision OCR items: {len(items)}')
print('By section:', sections)
# Show first 10
for i in items[:10]:
    print(f'  {i[\"description\"]}: {i[\"amount\"]}')
"
```

Expected: Mix of income, expenses, assets, liabilities sections.

## Output File
Write to `test-results/dynamic/agent3-extraction.md`:

```markdown
# Agent 3: Extraction Results

## Summary
| Document | Year | Items Extracted | Status | Time |
|----------|------|----------------|--------|------|
| BS-Dynamic 2022.xlsx | FY22 | N | ✅/❌ | Xs |
| Notes to Financials.pdf | FY22 | N | ✅/❌ | Xs |
| ITR BS P&L.pdf | FY22 | N | ✅/❌ | Xs |
| ITR PL & BS.pdf | FY23 | N | ✅/❌ | Xs |
| Notes..pdf | FY23 | N | ✅/❌ | Xs |
| Audited Financials FY-2024.pdf | FY24 (VISION OCR) | N | ✅/❌ | Xs |
| Provisional 31.03.25.xlsx | FY25 | N | ✅/❌ | Xs |

**Total items extracted:** N
**Client ID:** ...
**Report ID:** ...
**FY24 Doc ID:** ...

## Vision OCR Validation (FY24)
- Extractor used: OcrExtractor ✅ / PdfExtractor ❌
- Item count: N (gate: > 50)
- Ambiguity questions: N items
- Sample items from FY24: [list 5]

## Ambiguity Questions Found
[List all items with ambiguity_question set]

## IDs for Subsequent Agents
- CLIENT_ID: ...
- REPORT_ID: ...
- FY24_DOC_ID: ...
```

## Gate Conditions
- FY24 must produce > 50 items — hard gate, STOP if not met
- Total items > 135 — soft gate, continue with warning if not met
- All 7 documents must complete without "failed" status

Pass these IDs to orchestrator for use in Agents 4, 5, 6:
- CLIENT_ID
- REPORT_ID
- All document IDs
