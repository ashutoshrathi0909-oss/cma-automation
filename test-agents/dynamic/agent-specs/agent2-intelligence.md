# Agent 2: Document Intelligence

## Your Job
Analyze all Dynamic Air Engineering documents BEFORE uploading them to the app. Confirm each file exists, is readable, and identify the industry and document type. This manifest prevents surprises during extraction.

## Working Directory
`C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2`

## Base Document Path
`DOCS\Financials\`

## Documents to Inspect

### FY 2021-22 (Audited)
1. `DOCS\Financials\FY_22\Financials\BS-Dynamic 2022 - Companies Act.xlsx`
   - Check: file exists, readable with openpyxl
   - Run: `docker compose exec backend python -c "import openpyxl; wb = openpyxl.load_workbook('/app/DOCS/Financials/FY_22/Financials/BS-Dynamic 2022 - Companies Act.xlsx', data_only=True); print('Sheets:', wb.sheetnames)"`
   - Expected: prints sheet names without error

2. `DOCS\Financials\FY_22\Financials\Notes to Financials.pdf`
   - Check: file exists
   - Run pdfplumber text extraction (first page only):
   ```bash
   docker compose exec backend python -c "
   import pdfplumber
   with pdfplumber.open('/app/DOCS/Financials/FY_22/Financials/Notes to Financials.pdf') as pdf:
       print('Pages:', len(pdf.pages))
       text = pdf.pages[0].extract_text()
       print('Text extractable:', bool(text))
       print('Sample:', (text or '')[:200])
   "
   ```
   - Expected: text_extractable = True (this is a digitally created PDF)

3. `DOCS\Financials\FY_22\Financials\ITR BS P&L.pdf`
   - Same check as above

### FY 2022-23 (Audited)
4. `DOCS\Financials\FY-23\ITR PL & BS.pdf`
   - Same pdfplumber check

5. `DOCS\Financials\FY-23\Notes..pdf`
   - Same pdfplumber check

### FY 2023-24 (Audited — SCANNED)
6. `DOCS\Financials\FY-24\Audited Financials FY-2024 (1).pdf`
   - This MUST be confirmed as a scanned (image-only) PDF
   - Run:
   ```bash
   docker compose exec backend python -c "
   import pdfplumber
   with pdfplumber.open('/app/DOCS/Financials/FY-24/Audited Financials FY-2024 (1).pdf') as pdf:
       print('Pages:', len(pdf.pages))
       text = pdf.pages[0].extract_text()
       print('Text extractable:', bool(text and len(text.strip()) > 50))
       print('Sample:', (text or 'EMPTY')[:100])
   "
   ```
   - **Expected:** Pages: 33, Text extractable: False (or very minimal garbled text)
   - This confirms OcrExtractor (Vision) will be used, not PdfExtractor

### FY 2024-25 (Provisional)
7. `DOCS\Financials\FY2025\Provisional financial 31.03.25 (3).xlsx`
   - Check: readable with openpyxl
   - Run sheet inspection

## Industry Detection
From the FY25 provisional Excel, extract 5 line item descriptions and classify industry:
- If items include "Wages", "Power", "Raw Materials", "Factory" → Manufacturing ✅
- If items include "Purchases", "Resale", "Trading stock" → Trading
- If items include "Professional fees", "Consulting" → Services

Run:
```bash
docker compose exec backend python -c "
import openpyxl
wb = openpyxl.load_workbook('/app/DOCS/Financials/FY2025/Provisional financial 31.03.25 (3).xlsx', data_only=True)
for sheet in wb.sheetnames:
    ws = wb[sheet]
    print(f'Sheet: {sheet}')
    for row in ws.iter_rows(min_row=1, max_row=30, values_only=True):
        if any(cell for cell in row if cell):
            print(row)
    print('---')
"
```

## File Size Check
Large file = likely scanned PDF (more data per page as image):
```bash
ls -lh "DOCS/Financials/FY-24/Audited Financials FY-2024 (1).pdf"
```
Expected: > 5 MB for a 33-page scanned document.

## Output File
Write to `test-results/dynamic/agent2-manifest.json`:

```json
{
  "agent": "2-intelligence",
  "company": "Dynamic Air Engineering",
  "industry_detected": "Manufacturing",
  "industry_confidence": "HIGH",
  "industry_evidence": ["line item 1", "line item 2", "line item 3"],
  "documents": [
    {
      "file": "BS-Dynamic 2022 - Companies Act.xlsx",
      "year": "FY22",
      "type": "Excel",
      "extractor": "ExcelExtractor",
      "sheets": ["Sheet1", "BS", "PL"],
      "readable": true,
      "notes": ""
    },
    {
      "file": "Notes to Financials.pdf",
      "year": "FY22",
      "type": "PDF_text",
      "extractor": "PdfExtractor",
      "pages": 0,
      "text_extractable": true,
      "readable": true,
      "notes": ""
    },
    {
      "file": "ITR BS P&L.pdf",
      "year": "FY22",
      "type": "PDF_text",
      "extractor": "PdfExtractor",
      "pages": 0,
      "text_extractable": true,
      "readable": true,
      "notes": ""
    },
    {
      "file": "ITR PL & BS.pdf",
      "year": "FY23",
      "type": "PDF_text",
      "extractor": "PdfExtractor",
      "pages": 0,
      "text_extractable": true,
      "readable": true,
      "notes": ""
    },
    {
      "file": "Notes..pdf",
      "year": "FY23",
      "type": "PDF_text",
      "extractor": "PdfExtractor",
      "pages": 0,
      "text_extractable": true,
      "readable": true,
      "notes": ""
    },
    {
      "file": "Audited Financials FY-2024 (1).pdf",
      "year": "FY24",
      "type": "PDF_scanned",
      "extractor": "OcrExtractor",
      "pages": 33,
      "text_extractable": false,
      "readable": true,
      "notes": "SCANNED — will use Claude Vision OCR (Phase 10)"
    },
    {
      "file": "Provisional financial 31.03.25 (3).xlsx",
      "year": "FY25",
      "type": "Excel",
      "extractor": "ExcelExtractor",
      "sheets": [],
      "readable": true,
      "notes": "Provisional financials"
    }
  ],
  "overall": "PASS",
  "ready_for_extraction": true
}
```

## Gate Condition
Report `PASS` if all 7 documents are readable and FY24 is confirmed as scanned.
Report `FAIL` with specific file if any document is missing or unreadable.
