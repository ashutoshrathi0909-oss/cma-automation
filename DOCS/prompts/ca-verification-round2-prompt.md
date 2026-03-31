# Prompt: Update CA Questionnaire — Round 2 Verification (Post-CA-Rules)

**Use this prompt in a fresh Claude Sonnet session. Copy-paste everything below.**

---

## TASK

Update the existing HTML questionnaire at `DOCS/ca-questionnaire.html` (1756 lines) by ADDING a new "Round 2" section at the end. Do NOT modify any existing questions — they are already answered and locked.

The Round 2 questions come from accuracy testing AFTER implementing the CA's first round of answers. We ran the classification AI on 3 companies (BCIPL, Dynamic Air, Mehta Computer) and interviewed the AI on every item it got wrong. These are the items where either:
- **GT vs AI disagree** — we need the CA to confirm which is correct
- **Context-dependent ambiguity** — the AI needs clarification on how to handle specific items

## DESIGN

Keep the exact same visual design, color scheme, and interaction patterns as the existing questionnaire:
- Same card layout, radio buttons, confidence selector, notes field
- Same navy (#1a365d) / orange (#e67e22) / green (#27ae60) colors
- Same collapsible sections, progress bar
- Same localStorage auto-save + JSON export

**BUT add these changes for Round 2:**
1. Add a visible separator banner: "ROUND 2 — Post-Accuracy-Test Verification (48 questions)"
2. The progress bar should show Round 2 progress separately (e.g., "Round 2: 0 of 48 answered")
3. Each question shows BOTH the GT answer AND the AI answer, and asks the CA to pick which is correct (or enter a different answer)
4. The JSON export should include both Round 1 and Round 2 answers in a single file

## QUESTION FORMAT FOR ROUND 2

Each Round 2 question card should show:

```
┌─────────────────────────────────────────────────────────┐
│ R2-A1. Selling & Distribution Expenses (BCIPL)          │
│                                                         │
│ Ground Truth says: Row 69 — Bad Debts              [GT] │
│ AI classified as:  Row 71 — Others (Admin)         [AI] │
│                                                         │
│ Which is correct?                                       │
│ ○ GT is correct → Row 69 (Bad Debts)                    │
│ ○ AI is correct → Row 71 (Others Admin)                 │
│ ○ BOTH wrong → Row [___] [field name dropdown]          │
│                                                         │
│ Confidence: ○ Certain  ○ Usually  ○ Depends             │
│ Notes: [___________________________________]            │
│                                                         │
│ Context: This item appeared in the P&L under            │
│ "Other Expenses" section.                               │
└─────────────────────────────────────────────────────────┘
```

## ROW REFERENCE (show as collapsible block at top of Round 2)

```
CMA Admin & Selling Expense Rows:
  R68 = Rent, Rates and Taxes
  R69 = Bad Debts
  R70 = Advertisements and Sales Promotions (includes: selling, distribution, brokerage, commission, carriage outward)
  R71 = Others (Admin & Selling) (catch-all for misc admin expenses)
  R72 = Repairs & Maintenance
  R73 = Audit Fees & Directors Remuneration
  R74 = (unused)
  R75 = Miscellaneous Expenses Written Off (NON-CASH write-offs only: preliminary expenses, pre-operative expenses)

CMA Employee Cost Rows:
  R45 = Wages (Manufacturing Expenses) — for manufacturing/construction companies
  R67 = Salary and staff expenses (Admin) — for trading/services companies

CMA Finance Rows:
  R83 = Interest on Fixed Loans / Term Loans
  R84 = Interest on Working Capital Loans
  R85 = Bank Charges
  R131-R133 = Short-term borrowings (balance sheet)

CMA Inventory Rows (Balance Sheet):
  R193-R198 = Inventories (Raw Materials, WIP, Finished Goods, Stores & Spares)
  R200 = Stocks-in-process (FORMULA CELL — do not classify into)
  R201 = Finished Goods (FORMULA CELL — do not classify into)

CMA Inventory Rows (P&L - Changes in Inventories):
  R53-R59 = Opening/Closing stock items
```

---

## ALL 48 QUESTIONS — GROUPED BY SECTION

### SECTION A: Admin Expense Bucket R68-R75 (12 questions)

**Context:** The AI and Ground Truth disagree on which admin row these items belong to. The most common pattern is that BCIPL's ground truth may have a -1 row offset (every GT row is 1 less than correct). We need the CA to confirm the correct row for each.

```
R2-A1:
  Item: "Selling & Distribution Expenses"
  Company: BCIPL
  GT says: R69 (Bad Debts)
  AI says: R71 (Others Admin)
  Options: R69, R70 (Advt & Sales Promo), R71, Other
  Note: CA previously confirmed Selling & Distribution → R70

R2-A2:
  Item: "Administrative & General Expenses"
  Company: BCIPL
  GT says: R69 (Bad Debts)
  AI says: R71 (Others Admin)
  Options: R69, R71, Other

R2-A3:
  Item: "Rates & Taxes"
  Company: BCIPL
  GT says: R70 (Advertisements and Sales Promotions)
  AI says: R68 (Rent, Rates and Taxes)
  Options: R68, R70, R71, Other

R2-A4:
  Item: "Bad debts written off"
  Company: BCIPL
  GT says: R70 (Advertisements and Sales Promotions)
  AI says: R69 (Bad Debts)
  Options: R69, R70, Other

R2-A5:
  Item: "Auditor's Remuneration - Statutory Audit"
  Company: BCIPL
  GT says: R70 (Advertisements and Sales Promotions)
  AI says: R73 (Audit Fees & Directors Remuneration)
  Options: R70, R73, Other
  Note: CA previously confirmed Directors Remuneration → R73. Does "Auditor's Remuneration" also go to R73?

R2-A6:
  Item: "Auditor's Remuneration - Tax Audit"
  Company: BCIPL
  GT says: R70 (Advertisements and Sales Promotions)
  AI says: R73 (Audit Fees & Directors Remuneration)
  Options: R70, R73, Other

R2-A7:
  Item: "Advances Written off"
  Company: BCIPL
  GT says: R70 (Advertisements and Sales Promotions)
  AI says: R69 (Bad Debts)
  Options: R69, R70, R75 (Misc Exp Written Off), Other
  Note: Is this a write-off (non-cash → R75) or a bad debt → R69?

R2-A8:
  Item: "Selling & Distribution Expenses" (different year/duplicate)
  Company: BCIPL
  GT says: R72 (Repairs & Maintenance)
  AI says: R70 (Advertisements and Sales Promotions)
  Options: R70, R72, Other

R2-A9:
  Item: "Brokerage & Commission"
  Company: Dynamic_Air
  GT says: R70 (Advertisements and Sales Promotions)
  AI says: R71 (Others Admin)
  Options: R70, R71, Other
  Note: CA previously confirmed Brokerage & Commission → R70

R2-A10:
  Item: "Carriage Outward"
  Company: Mehta_Computer
  GT says: R71 (Others Admin)
  AI says: R70 (Advertisements and Sales Promotions)
  Options: R70, R71, Other
  Note: CA previously confirmed Carriage Outward → R70

R2-A11:
  Item: "Sundry Balance W/off"
  Company: Mehta_Computer
  GT says: R71 (Others Admin)
  AI says: R75 (Miscellaneous Expenses Written Off)
  Options: R71, R75, R69 (Bad Debts), Other
  Note: Is "Sundry Balance Written Off" a non-cash write-off (→ R75) or a bad debt (→ R69) or just admin (→ R71)?

R2-A12:
  Item: "Professional tax"
  Company: Mehta_Computer
  GT says: R71 (Others Admin)
  AI says: R68 (Rent, Rates and Taxes)
  Options: R68, R71, Other
  Note: Professional Tax is a statutory levy. Does it go under Rates & Taxes (R68) or Others (R71)?
```

### SECTION B: Employee Cost — Industry Classification for Dynamic Air (7 questions)

**Context:** Dynamic Air Engineering is a manufacturing company. Our CA rules send manufacturing company employee items to R45 (Wages/Manufacturing), but the ground truth says R67 (Salary/Admin) for these items. We need the CA to confirm: for a manufacturing company like Dynamic Air, should employee costs go to R45 or R67?

**Also:** Two items are Balance Sheet provisions/liabilities (not P&L expenses), which should NOT go to R45 even for manufacturing companies.

```
R2-B1:
  Item: "(d) Contribution to EPF and ESI"
  Company: Dynamic_Air (Manufacturing)
  GT says: R67 (Salary and staff expenses — Admin)
  AI says: R45 (Wages — Manufacturing)
  Options: R45, R67, Other
  Note: CA previously said EPF/ESI → always R45. But GT says R67 for this company. Confirm?

R2-B2:
  Item: "(a) Salaries and incentives"
  Company: Dynamic_Air (Manufacturing)
  GT says: R67 (Salary)
  AI says: R45 (Wages)
  Options: R45, R67, Other
  Note: Is "Salaries and incentives" always R67 even for manufacturing? Or R45?

R2-B3:
  Item: "(c) Staff Welfare"
  Company: Dynamic_Air (Manufacturing)
  GT says: R67 (Salary)
  AI says: R45 (Wages)
  Options: R45, R67, Other

R2-B4:
  Item: "(e) Gratuity"
  Company: Dynamic_Air (Manufacturing)
  GT says: R67 (Salary)
  AI says: R45 (Wages)
  Options: R45, R67, Other
  Note: CA previously said Gratuity → always R45. But GT says R67. Confirm?

R2-B5:
  Item: "(c) Staff Welfare Expenses"
  Company: Dynamic_Air (Manufacturing)
  GT says: R67 (Salary)
  AI says: R45 (Wages)
  Options: R45, R67, Other

R2-B6:
  Item: "Provision for employee benefits (Gratuity)"
  Company: Dynamic_Air
  GT says: R153 (As Long Term Debt — Balance Sheet)
  AI says: R45 (Wages — P&L)
  Options: R153, R45, R249 (Creditors for Expenses), Other
  Note: This is a BALANCE SHEET provision, not a P&L expense. Should it go to R153 (Long-term provision) or elsewhere?

R2-B7:
  Item: "(c) Statutory Dues - (iii) ESI & PF Payable"
  Company: Dynamic_Air
  GT says: R246 (Other statutory liabilities)
  AI says: R45 (Wages — P&L)
  Options: R246, R45, R249 (Creditors for Expenses), Other
  Note: This is a BALANCE SHEET current liability (payable), not a P&L expense. Should it go to R246?
```

### SECTION C: Bill Discounting — Interest vs Borrowing (3 questions)

**Context:** The AI consistently classifies "Bill Discounting" items as R133 (outstanding bill discounting balance — a borrowing/liability), but the correct answer should be R83 or R84 (interest expense) when it appears in P&L finance costs.

```
R2-C1:
  Item: "Bill Discounting Charges"
  Company: BCIPL (P&L - Finance Costs)
  GT says: R83 (Interest on Fixed Loans / Term Loans)
  AI says: R133 (O/s bill discounting balance — Short-term borrowing)
  Options: R83, R84 (Interest on WC), R85 (Bank Charges), R133, Other
  Note: The CHARGE for bill discounting is an interest cost. The outstanding BALANCE is a borrowing. Which row for the P&L charge?

R2-C2:
  Item: "Inland LC Discounting"
  Company: BCIPL (Balance Sheet - Short-term Borrowings)
  GT says: R131 (From Indian Bank — short-term borrowing)
  AI says: R133 (O/s bill discounting balance)
  Options: R131, R133, Other
  Note: This is a BS item (borrowing), not P&L. Is "Inland LC Discounting" under general bank borrowings (R131) or specific bill discounting (R133)?

R2-C3:
  Item: "(b) Interest on Bill discounting & charges"
  Company: Dynamic_Air (P&L - Finance Costs)
  GT says: R84 (Interest on Working Capital Loans)
  AI says: R133 (O/s bill discounting balance)
  Options: R84, R83, R85, R133, Other
```

### SECTION D: Loan Processing Fee — R83/R84 vs R85 (2 questions)

**Context:** Our CA previously confirmed Loan Processing Fee → R85 (Bank Charges). But Dynamic Air's GT says R84 (WC Interest) in one case and R83 (TL Interest) in another. We need to verify: does the answer change based on loan type?

```
R2-D1:
  Item: "(a) Loan/Overdraft Processing Fee"
  Company: Dynamic_Air (P&L - Finance Costs)
  GT says: R84 (Interest on Working Capital Loans)
  AI says: R85 (Bank Charges)
  Options: R84, R85, Other
  Note: CA said R85 in Round 1. Is this still correct even for WC loan processing fees?

R2-D2:
  Item: "(a) Loan/Overdraft Processing Fee" (different year)
  Company: Dynamic_Air (P&L - Finance Costs)
  GT says: R83 (Interest on Fixed Loans / Term Loans)
  AI says: R85 (Bank Charges)
  Options: R83, R85, Other
  Note: Same item, different year. GT says R83 this time. Confirm R85 (CA's Round 1 answer)?
```

### SECTION E: Inventory / Stock Items (5 questions)

**Context:** Confusion between P&L stock items (Changes in Inventories, R53-R59) and Balance Sheet inventory items (Current Assets, R193-R201). Also, R200 and R201 are FORMULA CELLS that should never be classified into.

```
R2-E1:
  Item: "Raw Materials" (Balance Sheet - Current Assets - Inventories)
  Company: BCIPL
  GT says: R193 (Imported — BS Inventories)
  AI says: R42 (Raw Materials Consumed Indigenous — P&L)
  Options: R193, R194 (Indigenous — BS), R42, Other
  Note: This is a BS item showing inventory value, not P&L consumption. Which BS inventory row?

R2-E2:
  Item: "Scraps" (Balance Sheet - Current Assets - Inventories)
  Company: BCIPL
  GT says: R197 (Imported — BS)
  AI says: DOUBT
  Options: R197, R198 (Indigenous — BS), Other
  Note: Where does "Scraps" inventory go on the BS?

R2-E3:
  Item: "Finished Goods" (Balance Sheet - Current Assets)
  Company: BCIPL
  GT says: R200 (Stocks-in-process — FORMULA CELL)
  AI says: DOUBT
  Options: R195, R196, R200 (formula), R201 (formula), Other
  Note: R200 is a FORMULA CELL (=CXX). CA previously said "don't touch." But the GT maps here. Is the GT wrong?

R2-E4:
  Item: "Work-in-Progress" (Balance Sheet - Current Assets)
  Company: Dynamic_Air
  GT says: R200 (Stocks-in-process — FORMULA CELL)
  AI says: DOUBT
  Options: R195, R196, R200, Other
  Note: Same issue as E3. R200 is formula. Where should WIP inventory go?

R2-E5:
  Item: "To Opening Stock" (P&L - Changes in Inventories)
  Company: Mehta_Computer
  GT says: R53 (Stock in process Opening)
  AI says: R58 (Finished Goods Opening Balance)
  Options: R53, R55 (Raw Materials Opening), R58, Other
  Note: "Opening Stock" without qualifier — is it WIP (R53), Raw Material (R55), or Finished Goods (R58)?
```

### SECTION F: Other Items (19 questions)

**Context:** Various items where the AI and GT disagree. Some may be GT offset bugs, others may need CA clarification.

```
R2-F1:
  Item: "Other Materials Consumed"
  Company: BCIPL (P&L - Manufacturing)
  GT says: R41 (Raw Materials Consumed Imported)
  AI says: R49 (Others Manufacturing)
  Options: R41, R44 (Stores & Spares Indigenous), R49, Other
  Note: Is "Other Materials" raw material (R41) or stores & spares (R44) or manufacturing other (R49)?

R2-F2:
  Item: "Other Materials Consumed" (different context)
  Company: BCIPL
  GT says: R43 (Stores and spares consumed Imported)
  AI says: R49 (Others Manufacturing)
  Options: R43, R44, R49, Other

R2-F3:
  Item: "Employee Benefits Expense"
  Company: BCIPL (Manufacturing)
  GT says: R44 (Stores and spares consumed)
  AI says: R67 (Salary and staff expenses)
  Options: R44, R45 (Wages), R67, Other
  Note: GT says R44 (Stores & Spares)?! This seems like a GT bug. Employee Benefits should be R45 or R67, not R44.

R2-F4:
  Item: "Deferred Tax"
  Company: BCIPL
  GT says: R100 (Deferred Tax Liability)
  AI says: R100 (Deferred Tax Liability)
  Options: SAME — skip this (comparison bug, both correct)
  Note: AI and GT match! This is a comparison bug in our test. No action needed.

R2-F5:
  Item: "Long-term Borrowings (Secured)"
  Company: BCIPL (Balance Sheet)
  GT says: R136 (Term Loan Repayable in next year)
  AI says: R153 (As Long Term Debt)
  Options: R136, R153, R140, Other
  Note: "Long-term Borrowings (Secured)" — is this the full LT borrowing (R153) or specifically the current maturity portion (R136)?

R2-F6:
  Item: "Capital Advances"
  Company: BCIPL (Balance Sheet)
  GT says: R235 (Dues from directors)
  AI says: R223 (Other Advances / current assets)
  Options: R235, R236 (Advances to suppliers), R223, Other
  Note: GT says R235 (Dues from directors)?! Capital Advances to directors or to suppliers?

R2-F7:
  Item: "Other Non-Current Assets"
  Company: BCIPL (Balance Sheet)
  GT says: R236 (Advances to suppliers of RM)
  AI says: R238 (Other non current assets)
  Options: R236, R238, Other

R2-F8:
  Item: "Leave Encashment"
  Company: BCIPL (Balance Sheet - Current Liabilities)
  GT says: R243 (Advance received from customers)
  AI says: R249 (Creditors for Expenses)
  Options: R243, R249, R250 (Other current liabilities), Other
  Note: CA said in Round 1: Leave Encashment in BS → R249 (Creditors for Expenses). GT says R243 (Advances from customers)?!

R2-F9:
  Item: "Short-term Provisions"
  Company: BCIPL (Balance Sheet)
  GT says: R248 (Interest Accrued and Due)
  AI says: R250 (Other current liabilities)
  Options: R248, R249, R250, Other

R2-F10:
  Item: "Carriage Inwards"
  Company: Dynamic_Air (P&L - Manufacturing)
  GT says: R47 (Freight and Transport)
  AI says: R41 (Raw Materials Consumed)
  Options: R47, R41, Other
  Note: Carriage Inwards is cost of bringing materials in. R47 (Freight) seems correct. Confirm?

R2-F11:
  Item: "(3) Deferred tax Liability / (Asset)"
  Company: Dynamic_Air (Balance Sheet)
  GT says: R101 (Deferred Tax Asset)
  AI says: R159 (Deferred tax liability — long-term)
  Options: R101, R100 (DT Liability), R159, Other
  Note: Is this a DT Asset (R101) or DT Liability (R159)? The item says "Liability / (Asset)" — depends on sign.

R2-F12:
  Item: "Interest on PPF"
  Company: Mehta_Computer (P&L - Other Income)
  GT says: R34 (Others — Non-operating income)
  AI says: R30 (Interest Received)
  Options: R30, R34, Other
  Note: PPF interest is interest income. R30 (Interest Received) or R34 (Others)?

R2-F13:
  Item: "Packing Forwarding"
  Company: Mehta_Computer (P&L)
  GT says: R49 (Others Manufacturing)
  AI says: R47 (Freight and Transport)
  Options: R47, R49, R70 (Advt & Sales Promo — selling expense), Other

R2-F14:
  Item: "Transport Charges"
  Company: Mehta_Computer (P&L)
  GT says: R49 (Others Manufacturing)
  AI says: R47 (Freight and Transport)
  Options: R47, R49, Other

R2-F15:
  Item: "To Depreciation"
  Company: Mehta_Computer (Balance Sheet)
  GT says: R163 (Less Accumulated Depreciation)
  AI says: R56 (Depreciation — P&L)
  Options: R163, R56, Other
  Note: BS "Depreciation" is accumulated depreciation (R163), not P&L depreciation expense (R56). Confirm R163?

R2-F16:
  Item: "TDS Receivable"
  Company: Mehta_Computer (Balance Sheet)
  GT says: R219 (Advances recoverable in cash)
  AI says: R206 (Domestic Receivables — trade)
  Options: R219, R221 (Advance Income Tax), R206, Other
  Note: TDS receivable = tax deducted at source to be recovered. R219 (advance receivable) or R221 (advance tax)?

R2-F17:
  Item: "Gst Receivable"
  Company: Mehta_Computer (Balance Sheet)
  GT says: R219 (Advances recoverable in cash)
  AI says: R223 (Other Advances / current assets)
  Options: R219, R223, Other

R2-F18:
  Item: "Telephone Deposits"
  Company: Mehta_Computer (Balance Sheet)
  GT says: R237 (Security deposits with govt bodies)
  AI says: R222 (Prepaid Expenses)
  Options: R237, R238 (Other non-current assets), R222, Other
  Note: Telephone deposit paid to telecom company (govt/PSU). R237 (govt deposits) or R238 (other non-current)?

R2-F19:
  Item: "IT Refund Due 2021"
  Company: Mehta_Computer (Balance Sheet)
  GT says: R219 (Advances recoverable in cash)
  AI says: R221 (Advance Income Tax)
  Options: R219, R221, Other
  Note: Income Tax refund receivable. R221 (Advance Income Tax) seems more specific. Or R219 (general advance)?

R2-F20:
  Item: "FD Accrued Interest (reclassified from Investments)"
  Company: Mehta_Computer (Balance Sheet)
  GT says: R182 (Investment in Govt. Securities)
  AI says: R229 (Investments — current)
  Options: R182, R229, R30 (Interest Received — P&L), Other
  Note: Accrued interest on FD. Is this an investment asset (R182/R229) or an income receivable?
```

---

## JSON EXPORT FORMAT

The exported JSON should have this structure:
```json
{
  "round": 2,
  "ca_name": "...",
  "date": "...",
  "answers": {
    "R2-A1": {
      "item": "Selling & Distribution Expenses",
      "company": "BCIPL",
      "gt_row": 69,
      "ai_row": 71,
      "ca_answer": "gt" | "ai" | "other",
      "correct_row": 70,
      "correct_field_name": "Advertisements and Sales Promotions",
      "confidence": "certain" | "usually" | "depends",
      "notes": "...",
      "is_gt_bug": true | false
    },
    ...
  }
}
```

## IMPORTANT NOTES FOR THE HTML BUILDER

1. Keep ALL existing Round 1 content intact — just ADD Round 2 at the bottom
2. The Round 2 section should have its own collapsible sections (A through F)
3. For questions marked "skip" or "comparison bug" (like R2-F4), show them greyed out with a "No action needed" label
4. Add a "Round 2 Summary" section at the end that shows:
   - How many items: GT was correct / AI was correct / Both wrong
   - How many GT offset bugs confirmed
5. The existing JSON export button should now export BOTH Round 1 + Round 2 answers
6. Add a new export button: "Export Round 2 Only" that exports just the Round 2 answers

## EXISTING FILE

Read the existing `DOCS/ca-questionnaire.html` file first to understand the exact HTML/CSS/JS structure, then add Round 2 at the end following the same patterns.
