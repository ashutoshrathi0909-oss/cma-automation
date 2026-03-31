# CMA Automation System — Dynamic Air Engineering Test
# Master Execution Instructions

> **READ THIS ENTIRE FILE BEFORE DOING ANYTHING.**
> You are the **Orchestrator (Agent 0)**. Do NOT re-plan. Do NOT deviate.
> Execute exactly what is described here, in the exact order specified.
> When in doubt: follow this file, not your instincts.

---

## 1. WHO YOU ARE AND WHAT YOU DO

You are the **Orchestrator**. Your job:
1. Read this file completely before doing anything
2. Verify pre-requisites (section 3)
3. Execute agents in order, enforcing gates between each
4. Each agent writes its results to a file — you NEVER hold large results in context
5. After all agents complete, confirm `test-results/dynamic/DYNAMIC_TEST_REPORT.md` exists and show the user a summary

**Context window discipline (non-negotiable):**
- Every agent writes its full output to `test-results/dynamic/agentN-*.md` or `.json`
- You only track: agent name + PASS/FAIL + output file path
- You NEVER read an agent's full output into this conversation — only the summary line
- The final report is assembled by Agent 7, not by you from memory

---

## 2. SYSTEM STATE

```
Docker:         All 4 containers must be running
  backend:      http://localhost:8000
  frontend:     http://localhost:3002
  redis:        localhost:6379
  worker:       ARQ background task processor

Auth bypass:    DISABLE_AUTH=true (set in .env)
                Use these headers on ALL API calls:
                  X-User-Id: 00000000-0000-0000-0000-000000000001
                  X-User-Role: admin

Real test user: email=admin@cma.test  password=CmaAdmin@2024
                (Only for Agent 6 E2E test — requires real browser login)

Project root:   C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Backend port:   8000
Frontend port:  3002
```

---

## 3. PRE-REQUISITE CHECK (Do This First)

Before spawning any agent, verify these files exist:

```bash
# Check pre-scan outputs exist
ls "test-results/dynamic/dynamic_ground_truth.md" && echo "P1 OK" || echo "P1 MISSING"
ls "test-results/dynamic/dynamic_cma_known_values.json" && echo "P2 OK" || echo "P2 MISSING"
ls "test-results/dynamic/dynamic_cma_analysis.md" && echo "P2b OK" || echo "P2b MISSING"
```

If either file is MISSING:
- The pre-scan agents (P1, P2) have not completed yet
- Wait for them to finish before proceeding
- Do NOT proceed without these files — Agents 4 and 7 depend on them

Also verify Docker is running:
```bash
docker compose ps
```
All 4 containers must show "Up". If not: `docker compose up -d` and wait 30 seconds.

---

## 4. DOCUMENT MANIFEST (DO NOT DEVIATE)

### Company: Dynamic Air Engineering
**Industry: MANUFACTURING** (air handling equipment — engineering/fabrication company)

**Base path:** `C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\Financials\`

| # | File | Path (relative to base) | Year | Type | Extractor |
|---|------|------------------------|------|------|-----------|
| 1 | `BS-Dynamic 2022 - Companies Act.xlsx` | `FY_22/Financials/` | FY 2021-22 | Excel (Audited) | ExcelExtractor |
| 2 | `Notes to Financials.pdf` | `FY_22/Financials/` | FY 2021-22 | PDF text (Audited) | PdfExtractor |
| 3 | `ITR BS P&L.pdf` | `FY_22/Financials/` | FY 2021-22 | PDF text (ITR) | PdfExtractor |
| 4 | `ITR PL & BS.pdf` | `FY-23/` | FY 2022-23 | PDF text (Audited) | PdfExtractor |
| 5 | `Notes..pdf` | `FY-23/` | FY 2022-23 | PDF text (Notes) | PdfExtractor |
| 6 | `Audited Financials FY-2024 (1).pdf` | `FY-24/` | FY 2023-24 | **SCANNED PDF** | **OcrExtractor (Vision)** |
| 7 | `Provisional financial 31.03.25 (3).xlsx` | `FY2025/` | FY 2024-25 | Excel (Provisional) | ExcelExtractor |

### Documents to SKIP (do NOT upload)
- `Auditor Report.pdf` — narrative, no financial data
- `Form 3CA & 3CD.pdf` — tax form
- Any EMI schedule, sanction letter, bank statement — TL Sheet only (not tested here)
- `Advance Tax Q*.pdf` — advance tax challans

### Ground Truth Files
| File | Contains | Used By |
|------|---------|---------|
| `test-results/dynamic/dynamic_ground_truth.md` | Claude's direct scan of FY22/23/25 | Agent 7 |
| `test-results/dynamic/dynamic_cma_known_values.json` | All values from CMA Dynamic 23082025.xls | Agents 4, 5, 7 |
| `DOCS/Financials/CMA Dynamic 23082025.xls` | Human-prepared CMA (ground truth) | Agents 5, 7 |

---

## 4b. KNOWN CORRECT VALUES (for quick validation — all in LAKHS)

These are from `CMA Dynamic 23082025.xls` INPUT SHEET. Use to spot-check classification results.

| Row | CMA Field | FY22 | FY23 | FY24 | FY25 |
|-----|-----------|------|------|------|------|
| R22 | Domestic Sales | 46.079 | 69.437 | 67.150 | 77.579 |
| R42 | Raw Materials (Indigenous) | 29.900 | 56.489 | 48.455 | 52.245 |
| R45 | Factory Wages | 3.452 | 5.836 | 6.537 | 7.165 |
| R48 | Power, Coal, Fuel & Water | 0.672 | 0.957 | 0.818 | 1.197 |
| R56 | Depreciation (Mfg) | 3.222 | 3.225 | 3.086 | 1.981 |
| R67 | Salary & Staff Expenses | 0.280 | 0.520 | 0.547 | 1.188 |
| R83 | Interest on Term Loans | 1.990 | 2.292 | 3.084 | 0.940 |
| R85 | Bank Charges | 0.302 | 0.231 | 0.136 | 0.178 |
| R104 | Net Profit (PAT) | 0.789 | 0.693 | 0.390 | 0.966 |
| R242 | Sundry Creditors | 8.176 | 10.376 | 8.451 | 15.851 |
| R260 | Total Assets | 43.649 | 55.757 | 52.505 | 58.037 |

**SCALE NOTE:** App may store values in absolute rupees. Divide by 100,000 before comparing with above.
FY25 cross-check: Revenue in source Excel = ₹7,75,79,246 → ÷ 100,000 = **77.58 lakhs** ✅

---

## 4c. ACCURACY THRESHOLDS (from best practices research)

| Metric | Target | Source |
|--------|--------|--------|
| Numerical field Exact Match Rate | > 95% | FinanceBench / LandingAI |
| Vision OCR character error rate | < 1% | FinCriticalED benchmark |
| Tier 1 (fuzzy) classification accuracy | > 98% | Industry standard |
| Tier 2 (AI) classification accuracy | > 90% | Industry standard |
| Doubt/escalation rate | < 15% | CMA validation research |
| Silent misclassification rate | 0% | Non-negotiable |
| Sign inversion errors | 0% | Non-negotiable |

---

## 5. AGENT EXECUTION SEQUENCE

Execute agents in this EXACT order. Do not proceed past a HARD GATE if it fails.

```
AGENT 1: Infrastructure Health        → Gate: ALL checks pass
AGENT 2: Document Intelligence        → Gate: All 7 docs readable, FY24 confirmed scanned
AGENT 3: Extraction Pipeline          → Gate: FY24 > 50 items (hard), total > 135 (soft)
AGENT 4: Classification Quality       → Gate: ≥ 85% on key rows (warning only, not hard stop)
AGENT 5: Excel Generation             → Gate: File downloads, ≥ 80% rows match (warning)
AGENT 6: E2E Critical Path            → Gate: Steps 8+9 must succeed (confirm Mehta fixes)
AGENT 7: Three-Way Comparison         → No gate — assembles final report
```

### How to Spawn Each Agent
For each agent, provide the full contents of its spec file as context. The spec files are in:
`test-agents/dynamic/agent-specs/`

**Read the spec file, then spawn the agent with that content as its instructions.** Do not summarize — give the full spec.

---

## 6. GATES — WHAT TO DO IF THEY FAIL

| Gate | Condition | Your Action |
|------|-----------|------------|
| G1: Infrastructure | Any Docker check fails | STOP. Tell user to fix Docker/dependencies. Do NOT proceed. |
| G2: Document Intel | Any file unreadable | STOP. Tell user which file is missing/corrupt. |
| G3: FY24 Vision OCR | < 50 items from FY24 | STOP. Phase 10 regression. Report: extractor used, log output, item count. |
| G3b: Total items | < 135 total | WARNING. Continue but flag in report. |
| G4: Classification | < 70% accuracy | WARNING. Continue. Note root cause (probably NULL cma_input_row). |
| G5: Excel | < 60% rows match | WARNING. Continue. Note likely scale mismatch or classification bug. |
| G6: E2E steps 8+9 | Either fails | ERROR. Report exact failure — this is a regression from Mehta fixes. |

---

## 7. OUTPUT FILES TO TRACK

Keep a running list as agents complete:

| Agent | Output File | Status |
|-------|------------|--------|
| 1 | `test-results/dynamic/agent1-health.json` | pending |
| 2 | `test-results/dynamic/agent2-manifest.json` | pending |
| 3 | `test-results/dynamic/agent3-extraction.md` | pending |
| 4 | `test-results/dynamic/agent4-classification.md` | pending |
| 5 | `test-results/dynamic/agent5-excel.md` | pending |
| 6 | `test-results/dynamic/agent6-e2e.md` | pending |
| 7 | `test-results/dynamic/DYNAMIC_TEST_REPORT.md` | pending |

---

## 8. IDs TO TRACK (filled in during execution)

You will need to pass these between agents. Track them here:

- **CLIENT_ID:** (filled after Agent 3 Step 1)
- **REPORT_ID:** (filled after Agent 3 Step 2)
- **FY22_EXCEL_DOC_ID:** (filled after Agent 3 Doc 1 upload)
- **FY22_NOTES_DOC_ID:** (filled after Agent 3 Doc 2 upload)
- **FY22_ITR_DOC_ID:** (filled after Agent 3 Doc 3 upload)
- **FY23_ITR_DOC_ID:** (filled after Agent 3 Doc 4 upload)
- **FY23_NOTES_DOC_ID:** (filled after Agent 3 Doc 5 upload)
- **FY24_SCANNED_DOC_ID:** (filled after Agent 3 Doc 6 upload) ← most important
- **FY25_EXCEL_DOC_ID:** (filled after Agent 3 Doc 7 upload)

---

## 9. FINAL SUMMARY

When Agent 7 completes and `DYNAMIC_TEST_REPORT.md` exists, tell the user:

```
Dynamic Air Engineering test complete.

📊 Overall: N/8 agents PASS
📁 Full report: test-results/dynamic/DYNAMIC_TEST_REPORT.md

Quick summary:
- Extraction: N total items (FY24 Vision OCR: N items ✅/❌)
- Classification: N% accuracy on key manufacturing rows
- Excel match: N% of key rows within 1% of known values
- E2E fixes (Mehta): Generate button ✅/❌  Download ✅/❌

[Any critical issues found]
```

---

## 10. IMPORTANT NOTES

1. **FY24 is the key test** — it's a 33-page scanned PDF. The OcrExtractor (Phase 10) must handle it. Allow up to 15 minutes for extraction.

2. **Manufacturing ≠ Trading** — Dynamic makes/sells equipment. Expect non-zero values at Factory Wages (R45), Power (R48), Raw Materials (R42). These were zero or near-zero for Mehta Computers.

3. **Scale in CMA file** — The existing `CMA Dynamic 23082025.xls` likely uses **lakhs** (1 = ₹1 lakh = ₹1,00,000). If the app generates values in absolute rupees, multiply by 0.00001 before comparing. Agent 5 handles this.

4. **Notes to Accounts are critical** — For manufacturing, Notes contain the sub-breakdowns of factory wages, power, materials. If Notes PDFs extract poorly, classification of FY22 and FY23 will suffer.

5. **Context discipline** — Do NOT read large agent outputs into this context. Just track PASS/FAIL per agent. The report is assembled by Agent 7.

---

*Start with the Pre-Requisite Check (Section 3), then proceed to Agent 1.*
