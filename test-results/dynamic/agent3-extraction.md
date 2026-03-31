# Agent 3: Extraction Results

## Summary
| Document | Year | Items Extracted | Status | Time |
|----------|------|----------------|--------|------|
| BS-Dynamic 2022 - Companies Act.xlsx | FY22 | 1887 | ✅ | 5s (worker) |
| Notes to Financials.pdf | FY22 | 195 | ✅ | 155s |
| ITR BS P&L.pdf | FY22 | 166 | ✅ | 144s |
| ITR PL & BS.pdf | FY23 | 109 | ✅ | 103s |
| Notes..pdf | FY23 | 185 | ✅ | 143s |
| Audited Financials FY-2024 (1).pdf | FY24 (VISION OCR) | 290 | ✅ | 267s |
| Provisional financial 31.03.25 (3).xlsx | FY25 | 139 | ✅ | 20s |

**Total items extracted:** 2971
**Client ID:** 2640855e-9676-4318-a274-8e911b7fac5e
**Report ID:** 4ed0d73d-df26-48f2-8898-5ab7a6d0b0f3
**FY24 Doc ID:** 3c021d45-57a9-484f-ad37-8206c04b66e0

## Vision OCR Validation (FY24)
- Extractor used: OcrExtractor ✅ (all scanned PDFs route to OcrExtractor via is_scanned_pdf() detection)
- Item count: 290 (gate: > 50) ✅ PASSED
- Sections breakdown: assets: 143, liabilities: 50, expenses: 64, equity: 11, income: 16, unknown: 6
- Ambiguity questions: 4 items in FY24 document
- Sample items from FY24:
  1. Land - Gross Block AS ON 31-03-2024: 24942539.0
  2. Land - WDV AS ON 31-03-2024: 24942539.0
  3. Buildings - Gross Block AS ON 31-03-2023: 49799172.0
  4. Buildings - Additions Before Sep: 715965.0
  5. Buildings - WDV AS ON 31-03-2024: 46363624.0

## Fixes Applied During Extraction
1. **Mock user ID mismatch**: Fixed `_MOCK_ADMIN_USER.id` from `00000000-...` to `aaaaaaaa-...` to match DB FK constraint
2. **Storage MIME type**: Added `content-type` header to Supabase Storage upload (was defaulting to `text/plain`, rejected)
3. **DB schema mismatch**: `extracted_line_items` uses `source_text` column, but code inserted `description`/`raw_text`. Fixed extraction task and router with `from_db()` mapper
4. **Supabase 1000-row limit**: Added pagination in `get_line_items` endpoint
5. **pdf2image not installed**: Installed in worker container (was missing from Docker image)
6. **MAX_PAGES_PER_BATCH=15 caused token overflow**: Reduced to 5 pages per batch; increased max_tokens from 8192 to 16000
7. **CMA report `financial_years` NOT NULL**: Added auto-derivation from linked document years
8. **Worker not restarting on code changes**: Manually restarted worker after each code change

## Ambiguity Questions Found (23 total)
- [Doc2 FY22 Notes] Note 19 - Cost of Materials: Wages vs Other Manufacturing split needed
- [Doc2 FY22 Notes] Note 21 - Employee Benefits: Salary vs Wages split needed
- [Doc2 FY22 Notes] Note 23 - Repairs and Maintenance: breakdown needed
- [Doc2 FY22 Notes] Note 23 - Office Expenses: breakdown needed
- [Doc3 FY22 ITR] Raw Materials + Direct Costs combined: split needed
- [Doc3 FY22 ITR] Employee benefits not broken down
- [Doc3 FY22 ITR] Other expenses > 1 lakh no breakdown
- [Doc4 FY23 ITR] Trade Payables - MSME classification question
- [Doc4 FY23 ITR] Raw Materials + Direct Costs combined
- [Doc4 FY23 ITR] Employee benefits not broken down
- [Doc4 FY23 ITR] Other expenses aggregated
- [Doc5 FY23 Notes] Trade Payables Others > 1 lakh
- [Doc5 FY23 Notes] Other Current Assets Others
- [Doc5 FY23 Notes] Raw Materials Consumed split needed
- [Doc5 FY23 Notes] Wages & Other Direct Expenses split
- [Doc5 FY23 Notes] Director remuneration split between directors
- [Doc6 FY24 Audited] Trade Payables MSME classification
- [Doc6 FY24 Audited] Raw Materials + Direct Costs combined
- [Doc6 FY24 Audited] Employee benefits no breakdown
- [Doc6 FY24 Audited] Other expenses > 1 lakh no breakdown
- [Doc6 FY24 Audited] (3 more FY24 items)

## IDs for Subsequent Agents
- CLIENT_ID: 2640855e-9676-4318-a274-8e911b7fac5e
- REPORT_ID: 4ed0d73d-df26-48f2-8898-5ab7a6d0b0f3
- FY24_DOC_ID: 3c021d45-57a9-484f-ad37-8206c04b66e0
- Doc1 (FY22 Excel): 976dd02c-814f-4ca2-a0dc-eab252530717
- Doc2 (FY22 Notes): 51821178-160a-4f5f-bfb9-51e873181c10
- Doc3 (FY22 ITR): 286129f7-b0b8-44d6-803a-36a5e8422a11
- Doc4 (FY23 ITR): 72ebeadc-d4ed-47fa-8fc8-a2492657d976
- Doc5 (FY23 Notes): 19ba296d-5edf-4f37-ae4c-9e287b629a22
- Doc6 (FY24 Audited): 3c021d45-57a9-484f-ad37-8206c04b66e0
- Doc7 (FY25 Provisional): b173641a-c660-45af-915a-b45aeb523b4d
