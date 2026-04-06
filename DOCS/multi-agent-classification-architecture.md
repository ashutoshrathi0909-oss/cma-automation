# Multi-Agent CMA Classification Architecture

## Status: PLANNING — Not yet implemented

## Problem Statement

The current single-agent classifier (DeepSeek V3) receives ONE prompt with 250+ CMA rows, 597 golden rules, and industry-specific exceptions. It can't hold all rules in working memory, so it:
- Defaults to "Others Admin" (R71) for anything it's unsure about
- Doubts items it could classify if it had focused context
- Misroutes manufacturing items to admin sections
- Can't classify individual bank loan accounts (sees them as unknown)

On BCIPL FY2023 (230 items): 56 classified, 174 doubted. Of 15 items matchable to ground truth, 9 correct (60%).

## Solution: Specialized Multi-Agent Pipeline

Replace the single classifier with 5 agents: 1 router + 4 specialists. Each specialist sees only its section's CMA rows and rules, enabling deeper expertise.

```
                         ALL EXTRACTED ITEMS (batch)
                                │
                                ▼
                    ┌───────────────────────┐
                    │     ROUTER AGENT      │  1 API call for all items
                    │                       │
                    │  Input: all items     │
                    │  Output: 4 buckets    │
                    │    + skip bucket      │
                    └───────────┬───────────┘
                                │
              ┌─────────┬───────┴────┬──────────┐
              ▼         ▼            ▼          ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ P&L      │ │ P&L      │ │ B/S      │ │ B/S      │
        │ INCOME   │ │ EXPENSES │ │ LIABS    │ │ ASSETS   │
        │ R22-R34  │ │ R41-R108 │ │ R110-160 │ │ R161-258 │
        │ 9 rows   │ │ 42 rows  │ │ 22 rows  │ │ 58 rows  │
        │ 52 rules │ │ 350 rules│ │ 84 rules │ │ 111 rules│
        └─────┬────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
              │            │            │             │
              │      1 API call    1 API call    1 API call
              │       per agent     per agent     per agent
              └────────────┴────────┬───┴────────────┘
                                    ▼
                            ┌──────────────┐
                            │   COMBINER   │  Pure code, no AI
                            │ Merge + save │
                            └──────────────┘
```

**Total: 5 API calls** (1 router + 4 specialists) instead of current 230 individual calls.

---

## Model Choice: Gemini 2.5 Flash via OpenRouter

| Aspect | DeepSeek V3 (current) | Gemini 2.5 Flash (proposed) |
|--------|----------------------|----------------------------|
| Context window | 64K tokens | **1M tokens** |
| Input cost | $0.27/M tokens | **$0.075/M** (3.5x cheaper) |
| Output cost | $1.10/M tokens | **$0.30/M** (3.5x cheaper) |
| JSON schema | Needs coaxing | **Native strict mode** |
| Batch capacity | ~5-10 items/call | **50-60 items/call** |
| Via OpenRouter | `deepseek/deepseek-chat` | `google/gemini-2.5-flash-preview` |

**Cost estimate for BCIPL (230 items):**
- Current: 230 x DeepSeek calls ~ $0.15-0.20
- New: 5 x Gemini Flash calls ~ **$0.01-0.02** (10x cheaper)

The 1M context window means each specialist can have ALL its CMA rows, ALL golden rules, full Indian accounting knowledge, AND a batch of 50-60 items in a single call.

---

## Component 1: Router Agent

### Purpose
Receives ALL extracted items for a document. Assigns each to one of 4 buckets or marks as "skip" (junk). Runs as a single API call.

### Input
```json
{
  "industry_type": "manufacturing",
  "items": [
    {"id": "item-001", "description": "Revenue from Operations", "amount": 1049700540, "section": "income", "source_sheet": "P & L Ac", "page_type": "face"},
    {"id": "item-002", "description": "Axis Bank Term Loan No. 879974", "amount": 7072348, "section": "long term borrowings", "source_sheet": "Notes BS (2)", "page_type": "notes"},
    {"id": "item-003", "description": "Mr. Chaitra Sundaresh", "amount": 1547100, "section": "equity shares", "source_sheet": "Notes BS (1)", "page_type": "notes"}
  ]
}
```

### Output
```json
{
  "routing": [
    {"id": "item-001", "bucket": "pl_income", "reason": "Revenue line from P&L"},
    {"id": "item-002", "bucket": "bs_liability", "reason": "Term loan under borrowings"},
    {"id": "item-003", "bucket": "skip", "reason": "Person name, not a financial line item"}
  ]
}
```

### Routing Signals (what the router uses to decide)
1. **source_sheet** — strongest signal
   - "P & L", "P&L", "Trading" → P&L agents
   - "BS", "Balance Sheet" → B/S agents
   - "Notes to P & L" → P&L agents
   - "Notes BS" → B/S agents
   - "Cash Flow" → skip (CMA doesn't use cash flow items)
2. **section** header from extraction
   - "income", "revenue", "sales" → pl_income
   - "expenses", "manufacturing", "admin" → pl_expense
   - "assets", "fixed assets", "current assets" → bs_asset
   - "liabilities", "equity", "borrowings" → bs_liability
3. **description** keywords — tiebreaker
4. **page_type** — face items flagged for potential skipping by specialists

### Skip Rules (junk filtering)
The router also filters items that should never reach classification:
- Person names (shareholder lists)
- Formula references: "(A + B)", "(i)", "(ii)"
- Opening/closing balance lines
- Ageing schedule rows: "Less than 1 year", "6 months to 1 year"
- Cash flow statement items (not used in CMA)
- Sub-totals that duplicate their parent totals

---

## Component 2: P&L Income Agent

### CMA Rows (9 rows)
| Row | Code | Name |
|-----|------|------|
| 22 | II_A1 | Domestic Sales |
| 23 | II_A2 | Export Sales |
| 25 | II_A4 | Less Excise Duty and Cess |
| 29 | II_B1 | Dividends received from Mutual Funds |
| 30 | II_B2 | Interest Received |
| 31 | II_B3 | Profit on sale of fixed assets / Investments |
| 32 | II_B4 | Gain on Exchange Fluctuations |
| 33 | II_B5 | Extraordinary income |
| 34 | II_B6a | Others (Non-Operating Income) |

### Golden Rules: 52 (7 CA-override + 45 legacy)

### Indian Accounting Knowledge Needed
- Revenue recognition under Schedule III
- Domestic vs Export split
- Job Work Charges RECEIVED = income (R22), not expense
- Sales Returns / Trade Discount = NEGATIVE amounts in R22
- GST/Excise treatment (pass-through, not revenue)
- Other Income types: interest earned, scrap sales, bad debts recovered, forex gain
- Subsidy/Government Grant → R33 (Extraordinary) in P&L, R125 in B/S
- Industry differences: manufacturing (product + job work), trading (resale), service (fee income)

---

## Component 3: P&L Expense Agent

### CMA Rows (42 rows — largest agent)
Covers: Manufacturing Expenses (R41-R59), Admin & Selling (R67-R77), Finance Charges (R83-R85), Non-Operating Expenses (R89-R93), Tax (R99-R101), Profit Appropriation (R106-R108)

### Golden Rules: 350 (largest set — this is where most classification errors occur)

### Indian Accounting Knowledge Needed (CRITICAL — most complex agent)

**Manufacturing vs Admin Split (the #1 source of errors):**
- MANUFACTURING companies:
  - Factory wages, PF, ESI, gratuity → R45 (Wages — manufacturing)
  - Power & Fuel → R46
  - Repairs to Plant & Machinery → R48
  - Job Work Charges PAID → R46 (Processing charges)
  - Stores & Spares Consumed → R44
  - Other factory expenses → R49 (Others Manufacturing)
  - Admin salaries → R67 (NOT R45)
  - Depreciation on factory assets → R56, on admin assets → R63
- TRADING companies:
  - NO manufacturing rows (R42-R49 unused except R42 for Purchases)
  - ALL wages/salary → R67
  - ALL depreciation → R61
  - Power & Fuel → R71 (admin expense, not manufacturing)
- SERVICE companies:
  - Similar to trading — no manufacturing rows

**Employee Benefit Expenses breakdown:**
- "Employee Benefit Expenses" is a TOTAL that contains: Salary + Wages + PF + ESI + Gratuity + Bonus + Leave Encashment
- For manufacturing: split between R45 (factory workers) and R67 (admin staff)
- For trading/service: all goes to R67

**Finance Cost breakdown:**
- Interest on Term Loans → R83
- Interest on Working Capital → R84
- Bank Charges → R85
- Bill Discounting → R84 (it's a form of WC finance)
- Loan Processing Fee → R85 (bank charge, not interest)

**Common misclassifications to prevent:**
- "Miscellaneous Expenses" → R71 (Others Admin), NOT R75 (non-cash write-offs)
- "Directors Remuneration" → R73 (Audit Fees), NOT R67 (Salary)
- "Insurance Premium" → R71 (Others Admin), NOT R49 (Others Manufacturing)
- "Licence & Subscription" → R71, NOT R68 (Rent Rates Taxes)
- "Stores & Spares" → R44 (specific manufacturing row), NOT R71
- "Job Work Charges (expense)" → R46, NOT R71

---

## Component 4: B/S Liability Agent

### CMA Rows (22 rows)
Covers: Share Capital (R116-R117), Reserves & Surplus (R121-R125), Working Capital (R131-R133), Term Loans (R136-R137), Debentures (R140-R141), Preference Shares (R144-R145), Other Debts (R148-R149), Unsecured Loans (R152-R154), Deferred Tax (R159)

### Golden Rules: 84

### Indian Accounting Knowledge Needed

**Individual loan accounts classification:**
- Any named bank account under "Long-term Borrowings" = R136 (Term Loans - Secured) or R137 (Term Loans - Unsecured)
- Examples: "Axis Bank Term Loan No. 879974", "HDFC TL A/c 12345" → ALL are R136
- The agent must classify by NATURE (term loan) not by specific account name
- "Sellers Credit" accounts = R136 (secured trade finance)
- Vehicle/equipment loans = R136

**Current maturities:**
- "Current maturities of long-term debt" = portion of TL due within 12 months
- Goes to R148 (Other Debts) or stays in R136 depending on CA preference
- BCIPL rule: current maturities → R148

**Working Capital vs Term Loan:**
- Cash Credit, Overdraft, Packing Credit → R131 (WC Bank Finance)
- Term Loan, Construction Loan, Equipment Loan → R136
- Bill Discounting facility → R131 (it's WC)

**Unsecured Loans:**
- Loans from directors, related parties → R152
- Inter-corporate deposits → R152

---

## Component 5: B/S Asset Agent

### CMA Rows (58 rows — second largest)
Covers: Fixed Assets (R162-R178), Investments (R182-R188), Inventories (R193-R201), Sundry Debtors (R206-R208), Cash & Bank (R212-R215), Loans & Advances (R219-R224), Non-Current Assets (R229-R238), Current Liabilities (R242-R250), Contingent Liabilities (R254-R258)

### Golden Rules: 111

### Indian Accounting Knowledge Needed

**Fixed Assets:**
- Gross Block, Accumulated Depreciation, Net Block → R162-R165
- Capital Work in Progress → R165
- Intangible Assets → R169-R172
- Depreciation schedule items (Additions, Disposals, "For the Year") → these are MOVEMENT rows, not standalone items. Agent should classify "For the Year" depreciation → R175 (Additions during the year) contextually.

**Inventories:**
- Raw Materials → R193
- Stores & Spares → R197
- Work in Progress → R200
- Finished Goods → R200
- Note: R200 and R201 are FORMULA rows in CMA.xlsm — never classify directly into them

**Trade Receivables:**
- Domestic Debtors → R206
- Export Debtors → R207
- If no split available, all to R206

**Current Liabilities (yes, these are in the Assets agent's range):**
- Sundry Creditors → R242
- Advance from Customers → R244
- Statutory Dues (PF, ESI, TDS, GST) → R245-R248
- Provisions (Leave Encashment, Gratuity) → R249

---

## Prompt Generation Strategy

Each agent's prompt has 5 layers:

### Layer 1: Identity + Role (hand-written, ~100 words)
Who the agent is, what section it handles, what industry_type applies.

### Layer 2: CMA Rows (auto-generated from canonical_labels.json)
Full list of rows with code, name, and section. Filtered to this agent's range only.

### Layer 3: Golden Rules (auto-generated from cma_golden_rules_v2.json)
CA-override rules shown first (highest priority). Legacy rules follow. Filtered to this agent's row range.

### Layer 4: Indian Accounting Knowledge (hand-written with CA review)
THIS IS THE SECRET SAUCE. Domain expertise specific to this agent's section. Includes:
- Schedule III terminology mappings
- Industry-specific rules (manufacturing vs trading vs service)
- Common misclassification traps
- Item disambiguation guidance

### Layer 5: Batch Input + Output Format (template)
JSON schema for batch input (array of items) and batch output (array of classifications).

### Auto-generation Script
A script reads the ground truth files and generates Layers 2, 3, 5 for each agent. Layer 4 is written by hand and reviewed by CA. The script outputs 5 prompt files:
- `prompts/router_prompt.md`
- `prompts/pl_income_prompt.md`
- `prompts/pl_expense_prompt.md`
- `prompts/bs_liability_prompt.md`
- `prompts/bs_asset_prompt.md`

---

## Orchestrator (Code, Not AI)

The orchestrator replaces the current `ClassificationPipeline` class:

```python
class MultiAgentPipeline:
    def classify_document(self, document_id, client_id, industry_type, ...):
        # 1. Fetch all verified line items
        items = fetch_items(document_id)
        
        # 2. Router call — ONE Gemini Flash call, all items
        buckets = self.router.route(items, industry_type)
        # buckets = {"pl_income": [...], "pl_expense": [...], 
        #            "bs_liability": [...], "bs_asset": [...], "skip": [...]}
        
        # 3. Call each specialist — ONE call per agent (batch)
        results = {}
        for bucket_name, bucket_items in buckets.items():
            if bucket_name == "skip":
                results["skip"] = [make_skip_result(item) for item in bucket_items]
                continue
            agent = self.agents[bucket_name]
            results[bucket_name] = agent.classify_batch(bucket_items, industry_type)
        
        # 4. Combine and save
        all_classifications = combine_results(results)
        save_to_db(all_classifications)
```

---

## Implementation Phases

### Phase 1: Foundation
- Switch model from DeepSeek to Gemini 2.5 Flash (one string change)
- Build prompt auto-generation script
- Generate base prompts for all 5 agents (Layers 1-3, 5)

### Phase 2: Router Agent
- Write router prompt with skip/junk filtering rules
- Test router on BCIPL data — verify bucket assignments
- Validate: items going to correct agents, junk filtered out

### Phase 3: P&L Agents (Income + Expense)
- Write Layer 4 (Indian accounting knowledge) for both P&L agents
- CA review of Layer 4 content
- Test against P&L items from BCIPL ground truth
- Iterate on prompts based on accuracy

### Phase 4: B/S Agents (Liability + Asset)
- Write Layer 4 for both B/S agents
- Special focus: individual loan account classification
- CA review of Layer 4 content
- Test against B/S items from BCIPL ground truth

### Phase 5: Integration + Testing
- Build MultiAgentPipeline orchestrator
- Wire into existing API (replace ClassificationPipeline)
- End-to-end test on BCIPL FY2023
- Accuracy comparison: old pipeline vs multi-agent

### Phase 6: Cross-Company Validation
- Test on all 9 GT companies (BCIPL, MSL, INPL, SLIPL, etc.)
- Different industries: manufacturing, trading, service
- Identify and fix any accuracy regressions

---

## Dependencies on Page-Type Work (Already Done)

The multi-agent system builds on the page_type infrastructure implemented in the current session:

| Feature | How Multi-Agent Uses It |
|---------|------------------------|
| `page_type` field on LineItem | Router uses it to flag face items for potential skipping |
| `source_sheet` persisted to DB | Router uses sheet name as primary routing signal |
| Dedup (notes > face) | Reduces duplicates before items reach the router |
| Cross-document awareness | Specialists know if note breakdowns exist elsewhere |

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Classification accuracy (vs GT) | ~60% | **85%+** |
| Doubt rate | 75% (174/230) | **<25%** |
| API calls per document | 230 | **5** |
| Cost per document | ~$0.15 | **~$0.02** |
| Items correctly skipped (junk) | 0 | **50+ per BCIPL** |

---

## Files That Will Change

| File | Change |
|------|--------|
| `backend/app/services/classification/multi_agent_pipeline.py` | NEW — orchestrator |
| `backend/app/services/classification/agents/router.py` | NEW — router agent |
| `backend/app/services/classification/agents/pl_income.py` | NEW — P&L income specialist |
| `backend/app/services/classification/agents/pl_expense.py` | NEW — P&L expense specialist |
| `backend/app/services/classification/agents/bs_liability.py` | NEW — B/S liability specialist |
| `backend/app/services/classification/agents/bs_asset.py` | NEW — B/S asset specialist |
| `backend/app/services/classification/agents/prompts/` | NEW — prompt templates |
| `backend/app/workers/classification_tasks.py` | Modified — use MultiAgentPipeline |
| `backend/app/config.py` | Modified — add Gemini model config |
| `scripts/generate_agent_prompts.py` | NEW — auto-generates prompts from GT |

The old `pipeline.py` and `scoped_classifier.py` are kept as fallback (config switch: `classifier_mode = "multi_agent"` vs `"scoped"`).
