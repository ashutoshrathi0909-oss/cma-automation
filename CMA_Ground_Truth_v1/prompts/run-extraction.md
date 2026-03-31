# Master Prompt: Build Ground Truth Database (v2 — Multi-Agent, Mixed Sources)

> **Paste this entire file into your Claude Code session** (opened in your CMA project folder).
> Claude will process the specified company using parallel agents per year.

---

## INSTRUCTIONS FOR CLAUDE

You are building a **ground truth database** for CMA (Credit Monitoring Arrangement) classification. Companies have mixed source files — Excel workbooks AND PDFs, sometimes both for the same year, sometimes different formats for different years.

### YOUR GOAL

For the specified company, extract every mapping between financial statement line items and CMA rows. Deploy **multiple parallel agents** — one per year, one per task — to prevent context overflow. Save structured extraction JSONs, then hand off to Opus reverse engineering (run separately by the user).

### CRITICAL CHANGE FROM v1

**DO NOT try to process everything in one context window.** The old approach blew up on large companies (MSL hit 32K token limit). Instead:
- Deploy **separate agents per financial year** for financial statement extraction
- Deploy **one agent for CMA extraction** (the CMA file covers all years)
- Each agent saves its output as a JSON file in the company folder
- Create a **SESSION_NOTES.md** documenting exactly what was extracted from which files
- The Opus reverse engineering step happens in a **separate new window** (user will start it manually)

---

### STEP-BY-STEP PROCESS

#### Phase 0: Scan & Plan

1. **Read company folder** — list ALL files with their sizes, types, and year groupings
2. **Classify each file** as: CMA workbook | Financial statements (Excel) | Financial statements (PDF) | Supporting document
3. **Create an extraction plan** — which agents to deploy, what each one will read, output filenames
4. **Show the plan to the user** before deploying agents

Example plan output:
```
EXTRACTION PLAN: Mehta Computer
================================
Agent 1 (Sonnet): CMA Extraction
  Input:  CMA 15092025.xls (parsed → JSON)
  Output: Mehta computer/mehta_cma_extraction.json

Agent 2 (Sonnet): FY2022 Financial Statements (Excel)
  Input:  2022/Mehta_Computers_financials_2022.xls (parsed → JSON)
  Output: Mehta computer/mehta_fs_2022.json

Agent 3 (Sonnet): FY2023 Financial Statements (Excel)
  Input:  2023/Mehta Computers financials 2023.xls (parsed → JSON)
  Output: Mehta computer/mehta_fs_2023.json

Agent 4 (Sonnet): FY2024 Financial Statements (Excel)
  Input:  2024/Mehta_Computers_financials_2024.xlsx (parsed → JSON)
  Output: Mehta computer/mehta_fs_2024.json

Agent 5 (Sonnet): FY2025 Financial Statements (PDF)
  Input:  2025/BSheet.pdf, 2025/PandL.pdf, 2025/TrialBal.pdf
  Output: Mehta computer/mehta_fs_2025.json

Total: 5 agents (deploy in parallel batches)
================================
```

#### Phase 1: Parse All Excel Files First

Before deploying agents, parse ALL Excel/XLS files to JSON:
```bash
# For .xlsx files
python scripts/parse_excel.py "path/to/file.xlsx" --output "Company/filename_parsed.json"

# For .xls files (legacy format)
python scripts/parse_xls.py "path/to/file.xls" --output "Company/filename_parsed.json"
```

Parse the CMA file and ALL year-wise Excel files. This gives agents readable JSON instead of binary Excel.

#### Phase 2: Deploy Extraction Agents (PARALLEL)

Deploy agents in **parallel batches**. Each agent gets:
- Its specific instructions (from the appropriate subagent prompt file)
- ONLY the data it needs (one year's worth, or just the CMA)
- A specific output filename to save its results

**BATCH 1: Deploy ALL agents simultaneously**

For each agent, use the Agent tool with `model: "sonnet"`. Structure the prompt as:

**CMA Extraction Agent:**
```
Include in prompt:
- Full instructions from prompts/prompts/subagent-2-cma-extractor.md
- The cma_template_reference.json content
- The parsed CMA Excel JSON data
- Ask it to SAVE output as {Company}/{company}_cma_extraction.json using the Write tool
```

**Per-Year Financial Statement Agents:**

For **Excel-based years**:
```
Include in prompt:
- Full instructions from prompts/prompts/subagent-2-cma-extractor.md (but for FS extraction, not CMA)
  OR: a simplified version — see the YEAR AGENT INSTRUCTIONS below
- The parsed year Excel JSON data
- The specific financial year (e.g., "2022-23")
- Ask it to SAVE output as {Company}/{company}_fs_{year}.json using the Write tool
```

For **PDF-based years**:
```
Include in prompt:
- Full instructions from prompts/prompts/subagent-1-sonnet-ocr.md
- Tell it to READ the PDF file(s) for that year using the Read tool
- The specific financial year
- Ask it to SAVE output as {Company}/{company}_fs_{year}.json using the Write tool
```

**IMPORTANT — Agent sizing rules to prevent context overflow:**
- If a PDF is **>10MB**, tell the agent to read it in page ranges (e.g., pages 1-20, then 21-40)
- If a year has **multiple PDFs** (e.g., BSheet.pdf + PandL.pdf + TrialBal.pdf), ONE agent handles all PDFs for that year
- If a year has **both Excel AND PDF**, deploy TWO agents — one for each format — they'll capture different detail levels
- **Maximum 5 agents per batch** — if you have more, deploy in 2 batches

#### Phase 3: Verify All Extractions

After all agents complete:
1. **Check each output file exists** and is valid JSON
2. **Quick-validate each extraction:**
   - CMA: How many non-zero rows? (expect 50-100)
   - Per year: Does P&L have revenue and expenses? Does BS balance?
3. **Flag any failed or incomplete extractions** — re-deploy those agents with adjusted parameters

#### Phase 4: Create SESSION_NOTES.md

**This is mandatory.** Create `{Company}/SESSION_NOTES.md` documenting exactly what was extracted:

```markdown
# {Company Name} — Extraction Session Notes
**Date:** {today's date}
**Extracted by:** Claude Code (Sonnet subagents)

## Source Files Inventory

| File | Type | Size | Year | Used By |
|------|------|------|------|---------|
| CMA 15092025.xls | CMA workbook | 473KB | All years | CMA Agent |
| 2022/financials.xls | Excel | 89KB | FY2021-22 | FS Agent 2022 |
| 2025/BSheet.pdf | PDF | 3.4KB | FY2024-25 | FS Agent 2025 |
| ... | ... | ... | ... | ... |

## Extraction Outputs

| Output File | Source(s) | Agent Type | Status | Key Stats |
|-------------|-----------|------------|--------|-----------|
| mehta_cma_extraction.json | CMA 15092025.xls | CMA Extractor | Complete | 78 rows, 3 years |
| mehta_fs_2022.json | financials_2022.xls | Excel FS | Complete | P&L: 25 items, BS: 30 items |
| mehta_fs_2025.json | BSheet.pdf, PandL.pdf | PDF OCR | Complete | P&L: 20 items, BS: 28 items |
| ... | ... | ... | ... | ... |

## Financial Years Covered
- FY2021-22: Source = Excel | Audited/Provisional: ___
- FY2022-23: Source = Excel | Audited/Provisional: ___
- FY2023-24: Source = Excel | Audited/Provisional: ___
- FY2024-25: Source = PDF  | Audited/Provisional: ___

## Company Profile
- **Industry:** {manufacturing/trading/services/etc}
- **Entity type:** {private_limited/partnership/etc}
- **Currency unit:** {rupees/lakhs/crores}
- **Special notes:** {any quirks discovered during extraction}

## Issues & Observations
- {List any extraction issues, missing data, format quirks}
- {Note any years with incomplete data}
- {Flag any unusually large or complex notes}

## Ready for Reverse Engineering
- [ ] All CMA rows extracted
- [ ] All financial years extracted
- [ ] All outputs validated
- [ ] Session notes complete
- **Next step:** Open a new Claude Code window and run the Opus reverse engineering prompt
```

#### Phase 5: Prepare Reverse Engineering Handoff

**DO NOT run the Opus reverse engineering yourself.** Instead, prepare the handoff:

1. List all extraction output files the Opus agent will need
2. Confirm all files are saved and valid
3. Tell the user:
```
Extraction complete for {Company}. All files saved in {Company}/ folder.

To run reverse engineering:
1. Open a NEW Claude Code window
2. Paste the reverse engineering prompt from prompts/prompts/main-opus-reverse-engineer.md
3. Tell it to read these files:
   - {Company}/{company}_cma_extraction.json
   - {Company}/{company}_fs_2022.json
   - {Company}/{company}_fs_2023.json
   - ... (list all)
   - canonical_labels.json
4. It will produce {company}_ground_truth.json
```

---

### YEAR AGENT INSTRUCTIONS (for Excel-based financial statement extraction)

When deploying a Sonnet agent to extract financial statements from an Excel file (not CMA, not PDF), use these instructions in the agent prompt:

```
You are extracting financial data from a company's Excel workbook for ONE specific financial year.

Extract:
1. PROFIT & LOSS: Every line item with description and amount
2. BALANCE SHEET: Every line item with description and amount
3. NOTES: Every note with sub-item breakdowns
4. DEPRECIATION SCHEDULE: If present
5. MANUFACTURING/TRADING ACCOUNT: If present

Rules:
- Preserve EXACT text descriptions (never normalize)
- Numbers in brackets () = negative
- Note the currency unit
- Extract ONLY the specified financial year
- Include note reference numbers

Save output as JSON using the Write tool to the specified filename.
Use the same JSON structure as defined in prompts/subagent-1-sonnet-ocr.md.
```

---

### HANDLING LARGE PDFs (>10MB)

For companies with very large PDFs (Dynamic Air FY24 = 15MB, INPL = 13-18MB each):

1. **Tell the agent to read in page ranges**: "Read pages 1-15 first, extract what you find, then read pages 16-30, etc."
2. **Split into 2 agents if needed**: Agent A reads pages 1-50 (P&L + BS), Agent B reads pages 51+ (Notes + Schedules)
3. **For PDFs with mixed content** (audit report + financials + notes): Tell the agent to skip the audit report text and focus on financial tables

---

### HANDLING COMPANIES WITH YEAR-WISE SUBFOLDERS

Some companies organize files by year (Mehta Computer: `2022/`, `2023/`, `2024/`, `2025/`).
Others have all files in the root (MSL, INPL).
Others organize by FY (Dynamic Air: `FY_22/`, `FY-23/`, `FY-24/`, `FY2025/`).

Adapt the plan to match the actual folder structure. Always use the full file path in agent prompts.

---

### IMPORTANT NOTES

1. **Deploy agents in parallel** — all year agents + CMA agent can run simultaneously
2. **Each agent saves its own output** — don't rely on agent return values for large data
3. **Context management** — each agent gets ONLY its year's data, never the full company
4. **Preserve exact text** from financial documents — never normalize or clean
5. **Validate amounts** — quick sanity checks after each agent completes
6. **Save SESSION_NOTES.md** — this is the audit trail for where data came from
7. **The Opus reverse engineering runs in a SEPARATE new window** — extraction agents are Sonnet only

### BEGIN

Tell me which company to process. I will scan the folder, create a plan, and deploy agents.
