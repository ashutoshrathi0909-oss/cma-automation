# CMA Automation System — Complete Build Specification

> **Purpose of this document:** This is a comprehensive specification for building a CMA (Credit Monitoring Arrangement) automation system. Feed this entire document to `/multi-plan` to generate a detailed implementation plan. Every decision has already been made — the planner should NOT re-decide the stack, architecture, or features. It should ONLY plan the build order and break it into parallel workstreams.

---

## 1. PROJECT OVERVIEW

### What is CMA?
CMA (Credit Monitoring Arrangement) is a standardized financial document that Indian businesses must prepare when applying for bank loans. It is prepared by Chartered Accountant (CA) firms. Every CA firm in India prepares dozens of these per year. The process is high-value, repetitive, and tedious.

### What This App Does
This web application automates CMA document preparation by:
1. Accepting uploaded financial documents (PDFs, Excel files) for a client
2. Extracting all financial line items from those documents
3. Classifying each line item into the correct CMA field using a reference mapping + AI
4. Presenting a verification + review interface for the CA to confirm/correct
5. Generating the final filled CMA Excel file (Sheet 1 + Sheet 2) that works with existing Excel macros

### Who Uses It
- **CA (Admin role):** Reviews classifications, corrects doubt items, approves final CMA, manages clients. This is the senior Chartered Accountant.
- **Employee (Operator role):** Uploads documents, initiates extraction, manages workflow, downloads final Excel.
- **Volume:** ~5 new CMAs per month + frequent corrections/updates to existing CMAs.

### Business Context
- Built first for internal use at a CA firm in India
- Potential to become a SaaS product for other CA firms later
- No open-source CMA automation tool exists — this is a novel product
- Commercial competitors (Gen CMA, EasyCMA) are desktop-only, manual entry, no AI

---

## 2. VERSION 1 SCOPE — STRICT BOUNDARIES

### What V1 INCLUDES:
- Client management (CRUD, search, industry type)
- Document upload and extraction (P&L, Balance Sheet, Notes to Accounts, Schedules)
- Loan repayment schedule upload and extraction
- AI-powered classification of line items into CMA fields
- Doubt report for uncertain classifications
- Side-by-side review interface with approve/correct per item
- Confidence dashboard (summary view)
- Learning system (store corrections, improve over time)
- CMA Excel output (.xlsm with preserved macros)
- Audit trail / change log
- Provisional to Audited conversion
- Annual rollover (guided process)
- Multi-user auth with roles (Admin/Employee)
- Docker containerization for local + production deployment

### What V1 STRICTLY EXCLUDES (do NOT build):
- No projections of any kind (no future year calculations)
- No Details Sheet interaction
- No bank ratio analysis or scrutiny
- No Razorpay/payment integration (internal tool for now)
- No multi-firm/multi-tenant support (single firm only in V1)
- No mobile app

---

## 3. THE CMA PROCESS (Domain Knowledge)

### How CMA Works Manually Today
1. CMA is a pre-decided Excel file (.xlsm) with many interconnected sheets
2. All sheets are connected through VBA macros and formulas
3. The CA manually fills ONLY 2 sheets:
   - **INPUT SHEET** — Historical financials (P&L rows 17-109, Balance Sheet rows 111-262)
   - **TL Sheet** — Loan repayment schedule (monthly rows, Term Loan + Working Capital columns)
4. After filling these 2 sheets, Excel macros automatically populate ALL other sheets (Form II, Form III, Form IV, Form V, Form VI, Cash Flows, Key Financials, Trend Analysis, Summary Spread, etc.)
5. The CA does a full human review before anything goes to the bank

### The Classification Challenge (The Hard Part)
- Financial statement line items use different terminology than what the CMA Excel expects
- Example: P&L says "Salary and Wages" → CMA field could be "Wages" (manufacturing) or "Salary and staff expenses" (service)
- Classification depends on client's industry type (manufacturing, service, trading, etc.)
- A reference file called "CMA Classification Excel" maps 384 financial statement terms to CMA fields
- When the reference doesn't cover a term, accounting knowledge and industry context are used
- When classification is genuinely uncertain, the CA MUST be consulted — the system must NEVER guess silently

### Key Safety Principle
**Wrong classifications in a CMA can have serious consequences for the bank loan application.** The doubt report and verification step are the core safety mechanisms. Human review is mandatory — the AI reduces work, it does not replace the CA's judgment.

---

## 4. REFERENCE FILES ANALYSIS (Already Analyzed)

### File 1: CMA Classification Excel (`DOCS/CMA classification.xls`)

**Structure:** 2 sheets, 5 columns each

**Sheet: Balance Sheet** (167 rows, 155 mapped items)
- Columns: Sr. No. | Items | CMA Classification Form III Item no. | CMA Broad Classification | Remarks
- Broad Classifications: Networth, Term Liability, Current Liability, Current Assets, Fixed Assets, Non-Current Assets, Investments, Intangible Asset, Depreciation, Fictitious Asset, Additional Info, Contingent Liability
- 55 unique CMA item mappings

**Sheet: Profit and Loss** (239 rows, 229 mapped items)
- Same column structure
- Broad Classifications: Cost of Sales, Selling/Gen/Admin Exp, Gross Sales, Sales, Interest, Non-operating Income, non-operating expenses, Tax, Dividend, Netted off against sales
- 26 unique CMA item mappings

**Total: 384 mapped items across both sheets. This is the AI's primary classification reference.**

### File 2: CMA Template (`DOCS/CMA.xlsm`)

**15 sheets total:** Details, TL, INPUT SHEET, Summary spread, Cash flows, Key Financials, Form_IV, Trend Analysis, Form_II, Form_III, Form_V, Form_VI, Financials improper, CMAcode, assumptions

**INPUT SHEET (289 rows, 13 columns) — What we fill:**

Header section (rows 1-16):
- A7: Name of the customer
- A8/B8-M8: Year headers (2023-2034)
- A9: Number of months (always 12)
- A10: Nature of Financials (Audited/Provisionals/Projected)
- A11: Financial Year ending (31st March)
- A12: Currency (INR)
- A13: Units
- A14: Auditors
- A15: Auditors Opinion

P&L Section (rows 17-109):
```
Row 22-23: Sales (Domestic, Exports)
Row 24: Sub Total (Sales)
Row 25: Less Excise Duty and Cess
Row 26: Net Sales
Row 29-34: Non-Operating Income (Dividends, Interest, Profit on sale, Exchange gains, Extraordinary, Others)
Row 35: Total Non-Operating Income
Row 40-51: Manufacturing Expenses:
  Row 41: Raw Materials Consumed (Imported)
  Row 42: Raw Materials Consumed (Indigenous)
  Row 43: Stores and spares consumed (Imported)
  Row 44: Stores and spares consumed (Indigenous)
  Row 45: Wages
  Row 46: Processing / Job Work Charges
  Row 47: Freight and Transportation Charges
  Row 48: Power, Coal, Fuel and Water
  Row 49: Others (manufacturing)
  Row 50: Repairs & Maintenance
  Row 51: Security Service Charges
Row 52: Sub Total Manufacturing
Row 53-54: Stock in process (Opening/Closing)
Row 55: WIP change in stock
Row 56: Depreciation (manufacturing)
Row 57: Cost of Production
Row 58-59: Finished Goods (Opening/Closing)
Row 60: FG change in stock
Row 61: Cost of Sales
Row 63-64: Manufacturing Expenses for CMA (Depreciation, Other)
Row 67-73: Admin & Selling Expenses:
  Row 67: Salary and staff expenses
  Row 68: Rent, Rates and Taxes
  Row 69: Bad Debts
  Row 70: Advertisements and Sales Promotions
  Row 71: Others (admin)
  Row 72: Repairs & Maintenance (admin)
  Row 73: Audit Fees & Directors Remuneration
Row 74: Sub Total Admin
Row 75-77: Amortisations (Misc expenses, Deferred revenue, Other)
Row 78: Sub Total Amortisations
Row 80: Total Expenditure
Row 83-85: Finance Charges (TL Interest, WC Interest, Bank Charges)
Row 86: Total Finance Charges
Row 89-93: Non-Operating Expenses (Loss on sale, Sundry balances, Exchange loss, Extraordinary, Others)
Row 94: Total Non-Operating Expenses
Row 96: Profit Before Tax
Row 99-101: Tax (Income Tax, Deferred Tax Liability, Deferred Tax Asset)
Row 102: Total Tax
Row 104: Net Profit (PAT)
Row 106: Brought forward from previous year
Row 107: Dividend
Row 108: Other Appropriation
Row 109: Balance carried to Balance Sheet
```

Balance Sheet Section (rows 111-262):
```
Row 113-114: Year headers + Nature of Financials (repeated)
Row 116-117: Share Capital (Issued/Subscribed, Share Application Money)
Row 118: Total Share Capital
Row 121-125: Reserves & Surplus (General Reserve, P&L balance, Share Premium, Revaluation, Other)
Row 126: Total Reserves
Row 131-132: Working Capital Bank Finance (Bank 1, Bank 2)
Row 134: Sub Total WC Finance
Row 136-137: Term Loans (Repayable in 1 year, After 1 year)
Row 138: Sub Total Term Loans
Row 140-141: Debentures (Repayable in 1 year, After 1 year)
Row 142: Sub Total Debentures
Row 144-145: Preference Shares (Repayable in 1 year, After 1 year)
Row 146: Sub Total Preference Shares
Row 148-149: Other Debts (Next 1 year, Balance)
Row 150: Sub Total Other Debts
Row 152-154: Unsecured Loans (Quasi Equity, Long Term, Short Term)
Row 155: Sub Total Unsecured
Row 157: Total Loans
Row 159: Deferred tax liability
Row 162-163: Fixed Assets (Gross Block, Less Accumulated Depreciation)
Row 164: Net Block
Row 165: Capital Work in Progress
Row 166: Total Fixed Assets
Row 169-172: Intangibles (Patents/goodwill, Misc expenditure, Deferred Tax Asset, Other)
Row 173: Total Intangibles
Row 175-178: Fixed Asset movements (Additions, Sale WDV, Profit on sale, Loss on sale)
Row 179: Total FA movements
Row 182-188: Investments (Govt Securities Current/Non-Current, Other Current/Non-Current, Group companies)
Row 189: Total Investments
Row 192-201: Inventories:
  Row 193-194: Raw Material (Imported, Indigenous)
  Row 195: Sub Total RM
  Row 197-198: Stores and Spares (Imported, Indigenous)
  Row 199: Sub Total Stores
  Row 200: Stocks-in-process
  Row 201: Finished Goods
Row 203: Total Inventories
Row 206-208: Sundry Debtors (Domestic, Export, >6 months)
Row 209: Total Debtors
Row 212-215: Cash and Bank (Cash, Bank, FD under lien, Other FD)
Row 216: Total Cash
Row 219-224: Loans & Advances (Recoverable, Suppliers, Income Tax, Prepaid, Other, Group companies)
Row 225: Total Loans & Advances
Row 228-238: Non-Current Assets (Group investments, Group advances, Debtors >6mo, Investments, FD, Directors dues, Capital goods suppliers, Security deposits, Other)
Row 239: Total Non-Current Assets
Row 242-250: Current Liabilities (Creditors for goods, Customer advances, Tax provision, Dividend, Statutory, Interest accrued not due, Interest accrued due, Creditors for expenses, Other)
Row 251: Total Current Liabilities
Row 254-258: Contingent Liabilities (Cumulative dividends, Gratuity, Disputed taxes, Bank guarantees, Other)
Row 260: Total Assets
Row 261: Total Liabilities
Row 262: Check (difference)
```

**TL Sheet (54 rows, 9 columns) — Loan Repayment:**
```
Row 2-3: Headers
  Columns B-E: Term Loan (OB, Payment, CB, Interest)
  Columns F-I: Working Capital Loan (OB, Additions, CB, Interest)
Row 4: Interest rate
Row 5: Opening balance date (31-Mar-2025)
Rows 6-53: Monthly rows from Apr 2025 to Mar 2029
  Each row: Date | OB | Payment | CB | Interest | OB | Additions | CB | Interest
```

**Data columns:** B through M represent years 2023-2034. For V1, we only fill historical years (typically columns B, C, D for 3 years or B, C for 2 years).

---

## 5. TECH STACK (All Decisions Final)

### Backend: Python FastAPI
- Framework: FastAPI with uvicorn
- Why: Best PDF/Excel processing ecosystem in Python. Async-first, modern, fast.

### Frontend: Next.js 15 (App Router)
- Why: Professional UI, excellent component ecosystem, Vercel hosting

### Database: PostgreSQL via Supabase
- Why: Relational data fits perfectly. Supabase provides hosted Postgres + Auth + Storage on free tier.
- Auth: Supabase Auth with role-based access (Admin/Employee)
- RLS: Row Level Security for data isolation

### Containerization: Docker + Docker Compose
- Backend + Frontend + Redis in docker-compose
- Hot reload for development (WATCHPACK_POLLING=true for Next.js on Windows)
- Same container runs locally and in production

### Hosting (Production)
- Backend: Railway (Mumbai region) — runs Docker natively
- Frontend: Vercel — best Next.js host
- CDN: Cloudflare (free)

---

## 6. KEY LIBRARIES (All Decisions Final)

### Python Backend Dependencies
```
fastapi                — API framework
uvicorn                — ASGI server
openpyxl               — Excel read/write (.xlsm with keep_vba=True to preserve macros)
xlrd                   — Read legacy .xls files (CMA Classification file is .xls)
pdfplumber             — PDF table extraction (text-based PDFs)
surya-ocr              — OCR for scanned PDFs (NOT pytesseract — 2x more accurate on financial docs)
rapidfuzz              — Fuzzy string matching (token_set_ratio for classification matching)
anthropic              — Claude API SDK (messages.parse() for structured output)
arq                    — Async task queue for background PDF processing
redis                  — ARQ broker
python-multipart       — FastAPI file uploads
pydantic               — Data validation + structured AI output schemas
supabase               — Supabase Python client (DB + Auth + Storage)
python-dotenv          — Environment variable management
pdf2image              — Convert PDF pages to images for surya-ocr (scanned PDFs only)
Pillow                 — Image processing (OCR preprocessing)
```

### Next.js Frontend Dependencies
```
@supabase/supabase-js       — Auth + DB client
@supabase/ssr               — Server-side Supabase for App Router
@tanstack/react-table       — Headless table for review UI
react-resizable-panels      — Split pane layout (side-by-side review)
react-dropzone              — File upload drag & drop
tailwindcss                 — Styling
shadcn/ui                   — UI component library (built on Radix + Tailwind)
lucide-react                — Icons
sonner                      — Toast notifications
recharts                    — Charts for confidence dashboard
```

### Infrastructure
```
docker + docker-compose     — Containerization
redis:7-alpine              — Task queue broker (Docker image)
```

---

## 7. ARCHITECTURE

### System Architecture
```
┌──────────────────────────────────────────────────────┐
│                 Next.js Frontend                      │
│  Dashboard │ Upload │ Review UI │ Doubt Report        │
│  Client Mgmt │ Confidence Dashboard │ Audit Trail     │
│                   Vercel / Docker                     │
└─────────────────────┬────────────────────────────────┘
                      │ REST API calls
┌─────────────────────▼────────────────────────────────┐
│          Docker Container: FastAPI Backend             │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Document    │  │ Classification│  │   Excel     │ │
│  │  Extractor   │  │   Engine     │  │  Generator  │ │
│  │             │  │              │  │             │ │
│  │ Excel→openpyxl│ │ Tier1:rapidfuzz│ │ openpyxl    │ │
│  │ PDF→pdfplumber│ │ Tier2:Haiku   │ │ keep_vba=True│ │
│  │ Scan→surya   │ │ Tier3:Sonnet  │ │ .xlsm output│ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  ARQ Worker  │  │   Learning   │  │  Audit Log  │ │
│  │  (async      │  │   System     │  │  Service    │ │
│  │   tasks)     │  │  (corrections│  │             │ │
│  │             │  │   → DB)      │  │             │ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
│                     Railway / Docker                   │
└────────┬──────────────┬──────────────────────────────┘
         │              │
  ┌──────▼──────┐  ┌───▼───────────────────┐
  │  Supabase   │  │   Claude API          │
  │  • Postgres │  │   • Haiku (classify)  │
  │  • Auth     │  │   • Sonnet (ambiguous)│
  │  • Storage  │  │   • messages.parse()  │
  └─────────────┘  └───────────────────────┘
```

### The 3-Tier Classification Pipeline
```
EXTRACTED LINE ITEM
       │
       ▼
┌──────────────────────────────────────┐
│ TIER 1: Fuzzy Match (FREE)           │
│ rapidfuzz.process.extractOne()       │
│ against 384 reference items          │
│ token_set_ratio, score_cutoff=85     │
│                                      │
│ Match found with score >= 85?        │
│   YES → Classification done (FREE)  │
│   NO  → Go to Tier 2                │
└──────────────────┬───────────────────┘
                   │ score < 85
                   ▼
┌──────────────────────────────────────┐
│ TIER 2: Claude Haiku (~₹0.05/item)  │
│ Send: line item + industry type +   │
│       top 5 fuzzy matches +         │
│       CMA field options             │
│                                      │
│ Confidence >= 0.8?                   │
│   YES → Classification done         │
│   NO  → Go to Tier 3                │
└──────────────────┬───────────────────┘
                   │ confidence < 0.8
                   ▼
┌──────────────────────────────────────┐
│ TIER 3: Doubt Report                 │
│ Add to doubt report with:            │
│   • Line item text                   │
│   • Amount                           │
│   • AI's best guess                  │
│   • Confidence score                 │
│   • Reason for uncertainty           │
│   • Top 3 possible CMA fields       │
│                                      │
│ CA must manually resolve this item   │
└──────────────────────────────────────┘
```

### Document Extraction Pipeline
```
UPLOADED DOCUMENT
       │
       ├── .xlsx / .xls file?
       │      │
       │      ▼
       │   openpyxl / xlrd
       │   → Perfect extraction (100% accurate)
       │   → Go to VERIFICATION SCREEN
       │
       ├── Native PDF (text-selectable)?
       │      │
       │      ▼
       │   pdfplumber.extract_table()
       │   → Good extraction (~90% accurate)
       │   → Go to VERIFICATION SCREEN
       │
       └── Scanned PDF (image-based)?
              │
              ▼
           surya-ocr
           → OCR extraction (~66% accurate)
           → Send OCR text to Claude Haiku for structuring
           → Go to VERIFICATION SCREEN

VERIFICATION SCREEN (MANDATORY — nothing proceeds without user confirmation)
┌──────────────────────────────────────────────┐
│ "Here's what I extracted. Please verify."     │
│                                               │
│ Revenue from Operations:  ₹4,52,30,000  [✓]  │
│ Other Income:             ₹12,45,000    [✓]  │
│ Cost of Materials:        ₹2,18,90,00?  [!]  │ ← Uncertain
│ Employee Benefits:        ₹45,60,000    [✓]  │
│                                               │
│ [Confirm All Correct]  [Edit & Confirm]       │
└──────────────────────────────────────────────┘
       │
       ▼ (only after user confirms)
  CLASSIFICATION PIPELINE (3-tier above)
```

---

## 8. DATABASE SCHEMA

### Tables

```sql
-- Users are managed by Supabase Auth
-- We store additional profile data here

CREATE TABLE user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'employee')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  industry_type TEXT NOT NULL CHECK (industry_type IN ('manufacturing', 'service', 'trading', 'other')),
  financial_year_ending TEXT DEFAULT '31st March',
  currency TEXT DEFAULT 'INR',
  notes TEXT,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,  -- Supabase Storage path
  file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'xlsx', 'xls')),
  document_type TEXT NOT NULL CHECK (document_type IN (
    'profit_and_loss', 'balance_sheet', 'notes_to_accounts',
    'schedules', 'loan_repayment_schedule', 'combined_financial_statement'
  )),
  financial_year INTEGER NOT NULL,  -- e.g., 2023, 2024
  nature TEXT NOT NULL CHECK (nature IN ('audited', 'provisional')),
  extraction_status TEXT DEFAULT 'pending' CHECK (extraction_status IN (
    'pending', 'processing', 'extracted', 'verified', 'failed'
  )),
  uploaded_by UUID REFERENCES auth.users(id),
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE extracted_line_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  source_text TEXT NOT NULL,          -- Original text from document
  amount DECIMAL(18,2),               -- Extracted amount
  page_number INTEGER,                -- Which page it was found on
  section TEXT,                        -- e.g., "P&L > Employee Benefits > Note 22"
  financial_year INTEGER NOT NULL,
  is_verified BOOLEAN DEFAULT FALSE,  -- User confirmed extraction is correct
  verified_by UUID REFERENCES auth.users(id),
  verified_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE classifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  line_item_id UUID NOT NULL REFERENCES extracted_line_items(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  cma_field_name TEXT NOT NULL,        -- e.g., "Raw Materials Consumed (Indigenous)"
  cma_sheet TEXT NOT NULL CHECK (cma_sheet IN ('input_sheet', 'tl_sheet')),
  cma_row INTEGER NOT NULL,            -- Exact row in INPUT SHEET (e.g., 42)
  cma_column TEXT,                     -- Column letter (B, C, D, etc.) based on year
  broad_classification TEXT,           -- e.g., "Cost of Sales", "Networth"
  classification_method TEXT NOT NULL CHECK (classification_method IN (
    'fuzzy_match', 'ai_haiku', 'ai_sonnet', 'manual', 'learned'
  )),
  confidence_score DECIMAL(3,2),       -- 0.00 to 1.00
  fuzzy_match_score INTEGER,           -- rapidfuzz score (0-100) if applicable
  is_doubt BOOLEAN DEFAULT FALSE,      -- Flagged for CA review
  doubt_reason TEXT,                   -- Why the system is uncertain
  ai_best_guess TEXT,                  -- What the AI suggested (if doubt)
  alternative_fields JSONB,            -- Top 3 alternative CMA fields
  status TEXT DEFAULT 'pending' CHECK (status IN (
    'pending', 'auto_classified', 'needs_review', 'approved', 'corrected'
  )),
  reviewed_by UUID REFERENCES auth.users(id),
  reviewed_at TIMESTAMPTZ,
  correction_note TEXT,                -- CA's reason for correction (audit trail)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE classification_corrections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  classification_id UUID NOT NULL REFERENCES classifications(id) ON DELETE CASCADE,
  client_id UUID NOT NULL REFERENCES clients(id),
  original_cma_field TEXT NOT NULL,
  corrected_cma_field TEXT NOT NULL,
  original_cma_row INTEGER NOT NULL,
  corrected_cma_row INTEGER NOT NULL,
  industry_type TEXT NOT NULL,
  source_text TEXT NOT NULL,           -- The original line item text
  correction_reason TEXT,
  corrected_by UUID REFERENCES auth.users(id),
  corrected_at TIMESTAMPTZ DEFAULT NOW()
);
-- This table feeds the learning system. Over time, we query:
-- "For industry=manufacturing, how was 'Salary and Wages' classified before?"
-- Corrections become future Tier 1 matches.

CREATE TABLE cma_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  financial_years JSONB NOT NULL,      -- e.g., [2022, 2023, 2024]
  year_natures JSONB NOT NULL,         -- e.g., {"2022":"audited","2023":"audited","2024":"provisional"}
  status TEXT DEFAULT 'draft' CHECK (status IN (
    'draft', 'extraction_pending', 'extraction_complete',
    'classification_pending', 'classification_complete',
    'review_in_progress', 'approved', 'excel_generated'
  )),
  total_line_items INTEGER DEFAULT 0,
  high_confidence_count INTEGER DEFAULT 0,
  medium_confidence_count INTEGER DEFAULT 0,
  needs_review_count INTEGER DEFAULT 0,
  output_file_path TEXT,               -- Path to generated .xlsm file
  generated_at TIMESTAMPTZ,
  approved_by UUID REFERENCES auth.users(id),
  approved_at TIMESTAMPTZ,
  created_by UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE cma_report_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cma_report_id UUID NOT NULL REFERENCES cma_reports(id) ON DELETE CASCADE,
  action TEXT NOT NULL,                -- e.g., "created", "classification_completed", "correction_applied", "excel_generated"
  action_details JSONB,               -- Detailed info about the action
  performed_by UUID REFERENCES auth.users(id),
  performed_at TIMESTAMPTZ DEFAULT NOW()
);
-- This is the audit trail. Every action is logged here.

CREATE TABLE cma_reference_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_sheet TEXT NOT NULL CHECK (source_sheet IN ('balance_sheet', 'profit_and_loss')),
  sr_no DECIMAL(5,1),
  item_name TEXT NOT NULL,             -- e.g., "Salary and Wages"
  cma_form_item TEXT NOT NULL,         -- e.g., "Item 5 (iv) : Direct Labour"
  broad_classification TEXT NOT NULL,  -- e.g., "Cost of Sales"
  remarks TEXT,
  cma_input_row INTEGER,              -- Mapped row in INPUT SHEET
  created_at TIMESTAMPTZ DEFAULT NOW()
);
-- This table is populated from the CMA Classification Excel on first setup.
-- 155 Balance Sheet items + 229 P&L items = 384 rows.

CREATE TABLE learned_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_text TEXT NOT NULL,           -- The financial statement term
  cma_field_name TEXT NOT NULL,        -- Where it was classified
  cma_input_row INTEGER NOT NULL,
  industry_type TEXT NOT NULL,
  times_used INTEGER DEFAULT 1,        -- How many times this mapping was confirmed
  last_used_at TIMESTAMPTZ DEFAULT NOW(),
  source TEXT NOT NULL CHECK (source IN ('correction', 'approval')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
-- This table grows as the CA makes corrections or approves classifications.
-- Tier 1 matching checks this table BEFORE the reference table.
-- More times_used = higher confidence in the mapping.

-- Indexes for performance
CREATE INDEX idx_clients_name ON clients(name);
CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_extracted_items_document_id ON extracted_line_items(document_id);
CREATE INDEX idx_extracted_items_client_id ON extracted_line_items(client_id);
CREATE INDEX idx_classifications_line_item_id ON classifications(line_item_id);
CREATE INDEX idx_classifications_client_id ON classifications(client_id);
CREATE INDEX idx_classifications_status ON classifications(status);
CREATE INDEX idx_corrections_industry ON classification_corrections(industry_type);
CREATE INDEX idx_corrections_source_text ON classification_corrections(source_text);
CREATE INDEX idx_reference_item_name ON cma_reference_mappings(item_name);
CREATE INDEX idx_learned_source_text ON learned_mappings(source_text);
CREATE INDEX idx_learned_industry ON learned_mappings(industry_type);
CREATE INDEX idx_cma_reports_client_id ON cma_reports(client_id);
CREATE INDEX idx_report_history_report_id ON cma_report_history(cma_report_id);

-- Row Level Security
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_line_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE classification_corrections ENABLE ROW LEVEL SECURITY;
ALTER TABLE cma_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE cma_report_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE cma_reference_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE learned_mappings ENABLE ROW LEVEL SECURITY;

-- RLS Policies: All authenticated users can access all data (single firm in V1)
-- In V2 (multi-firm), add firm_id column and restrict by firm
CREATE POLICY "Authenticated users can read all data" ON clients
  FOR SELECT USING (auth.uid() IS NOT NULL);
CREATE POLICY "Authenticated users can insert" ON clients
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "Authenticated users can update" ON clients
  FOR UPDATE USING (auth.uid() IS NOT NULL);
-- Repeat similar policies for all tables
-- Admin-only policies for DELETE operations
CREATE POLICY "Only admins can delete" ON clients
  FOR DELETE USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
  );
```

---

## 9. API ENDPOINTS

### Auth
```
POST   /api/auth/register          — Register new user (admin only can create employees)
POST   /api/auth/login             — Login
POST   /api/auth/logout            — Logout
GET    /api/auth/me                — Get current user profile
```

### Clients
```
GET    /api/clients                — List all clients (search, filter by industry)
POST   /api/clients                — Create new client
GET    /api/clients/:id            — Get client details with CMA history
PUT    /api/clients/:id            — Update client
DELETE /api/clients/:id            — Delete client (admin only)
```

### Documents
```
POST   /api/clients/:id/documents  — Upload document(s) for a client
GET    /api/clients/:id/documents  — List documents for a client
DELETE /api/documents/:id          — Delete a document
GET    /api/documents/:id/status   — Get extraction status
```

### Extraction & Verification
```
POST   /api/documents/:id/extract           — Trigger extraction (async, returns task_id)
GET    /api/tasks/:task_id/status            — Get extraction task progress
GET    /api/documents/:id/extracted-items    — Get extracted line items for verification
PUT    /api/extracted-items/:id              — Edit an extracted line item (fix amount/text)
POST   /api/documents/:id/verify             — Confirm all extracted items are correct
```

### Classification
```
POST   /api/cma-reports/:id/classify         — Trigger classification (async, returns task_id)
GET    /api/cma-reports/:id/classifications  — Get all classifications with confidence scores
GET    /api/cma-reports/:id/doubt-report     — Get only doubt items (needs_review)
PUT    /api/classifications/:id              — Approve or correct a classification
POST   /api/cma-reports/:id/bulk-approve     — Approve all high-confidence items at once
```

### CMA Reports
```
POST   /api/clients/:id/cma-reports          — Create new CMA report for client
GET    /api/clients/:id/cma-reports          — List CMA reports for client
GET    /api/cma-reports/:id                  — Get CMA report details + summary stats
GET    /api/cma-reports/:id/confidence       — Get confidence dashboard data
POST   /api/cma-reports/:id/generate-excel   — Generate final CMA Excel file
GET    /api/cma-reports/:id/download         — Download generated Excel file
GET    /api/cma-reports/:id/audit-trail      — Get audit trail / change log
```

### Provisional → Audited
```
POST   /api/cma-reports/:id/convert-provisional  — Start provisional to audited conversion
GET    /api/cma-reports/:id/conversion-diff       — Get diff between provisional and audited
POST   /api/cma-reports/:id/confirm-conversion    — Confirm the conversion
```

### Annual Rollover
```
POST   /api/clients/:id/rollover            — Start annual rollover process
GET    /api/clients/:id/rollover/preview     — Preview what rollover will do
POST   /api/clients/:id/rollover/confirm     — Confirm and execute rollover
```

### Reference Data
```
GET    /api/reference/cma-fields             — Get all CMA fields from classification reference
GET    /api/reference/cma-fields/:sheet      — Get fields for specific sheet (balance_sheet/pnl)
POST   /api/reference/import                 — Import CMA Classification Excel (one-time setup)
```

---

## 10. FRONTEND PAGES & COMPONENTS

### Pages (Next.js App Router)

```
/                           — Dashboard (client list, recent CMA reports, quick stats)
/login                      — Login page
/clients                    — Client list with search and filters
/clients/new                — Create new client form
/clients/[id]               — Client detail page (info + CMA history + documents)
/clients/[id]/upload        — Document upload page (drag & drop, year/type selection)
/clients/[id]/cma/new       — Start new CMA report (select years, mark audited/provisional)
/cma/[id]                   — CMA report overview (status, confidence dashboard)
/cma/[id]/verify            — Extraction verification screen (confirm extracted numbers)
/cma/[id]/review            — Side-by-side classification review (main review interface)
/cma/[id]/doubts            — Doubt report (only uncertain items, CA resolves here)
/cma/[id]/audit-trail       — Change log / audit trail
/cma/[id]/convert           — Provisional to audited conversion (diff view)
/clients/[id]/rollover      — Annual rollover wizard
/settings                   — App settings, user management (admin only)
```

### Key Components

```
<ClientCard />              — Client summary card for dashboard
<ClientForm />              — Create/edit client form
<DocumentUploader />        — Drag & drop file upload with year/type metadata
<ExtractionVerifier />      — Shows extracted line items, user confirms/edits amounts
<ConfidenceDashboard />     — Pie/bar chart: high/medium/needs review counts
<ClassificationReview />    — Side-by-side split pane:
                               Left: original line item from financial statement
                               Right: proposed CMA field + confidence
                               Actions: Approve / Correct / Flag
<DoubtReport />             — Table of uncertain items with AI best guess,
                               confidence, reason, dropdown to select correct field
<CMAFieldSelector />        — Searchable dropdown of all CMA fields for manual correction
<AuditTrail />              — Timeline/table of all actions on a CMA report
<ConversionDiff />          — Side-by-side diff: provisional vs audited figures
<RolloverWizard />          — Step-by-step guided annual rollover process
<ProgressTracker />         — Shows async task progress (extraction, classification)
```

---

## 11. CORE WORKFLOW (Step by Step)

### Complete CMA Preparation Flow

```
Step 1: CREATE CLIENT
  Employee creates client: name, industry type (manufacturing/service/trading)
  → Saved to clients table

Step 2: UPLOAD DOCUMENTS
  Employee uploads financial documents for 2-3 years:
    - P&L PDF/Excel for 2022 (audited)
    - P&L PDF/Excel for 2023 (audited)
    - P&L PDF/Excel for 2024 (provisional)
    - Balance Sheet with Notes for each year
    - Loan repayment schedule
  Each document tagged with: year, type, audited/provisional
  → Saved to documents table + Supabase Storage

Step 3: CREATE CMA REPORT
  Employee creates CMA report: selects years [2022, 2023, 2024]
  Marks nature: {2022: audited, 2023: audited, 2024: provisional}
  → Saved to cma_reports table

Step 4: EXTRACT (Async background task via ARQ)
  System processes each document:
    - Excel files → openpyxl reads perfectly
    - Native PDFs → pdfplumber extracts tables
    - Scanned PDFs → surya-ocr → Claude Haiku structures text
  → Line items saved to extracted_line_items table
  → Status updates via /tasks/:id/status endpoint
  → Frontend polls for progress

Step 5: VERIFY EXTRACTION (MANDATORY)
  Employee/CA sees verification screen:
    - All extracted line items with amounts
    - Uncertain items flagged with [!]
    - User confirms each item is correct or edits the value
  → is_verified = true for confirmed items
  → Cannot proceed to classification until all items verified

Step 6: CLASSIFY (Async background task via ARQ)
  For each verified line item:
    Tier 1: Check learned_mappings table (past corrections for same industry)
    Tier 1: Check cma_reference_mappings table (384 items) via rapidfuzz
    Tier 2: If no match ≥ 85, send to Claude Haiku with context
    Tier 3: If Haiku confidence < 0.8, add to doubt report
  → Classifications saved to classifications table
  → Confidence counts updated in cma_reports table

Step 7: CONFIDENCE DASHBOARD
  CA sees summary before diving in:
    - Total items: 85
    - High confidence (auto-approved): 52 (61%)
    - Medium confidence (review recommended): 21 (25%)
    - Needs CA input (doubt items): 12 (14%)

Step 8: REVIEW CLASSIFICATIONS
  CA uses side-by-side review interface:
    Left panel: "Salary and Wages — ₹45,60,000 — from P&L Note 22"
    Right panel: "Mapped to: Wages (Row 45) — Confidence: 92%"
    Actions: [Approve] [Correct] [Flag]

  For corrections:
    CA selects correct CMA field from dropdown
    Optionally adds reason for correction
    → Correction saved to classification_corrections table
    → learned_mappings table updated (learning system)
    → Audit trail entry created

Step 9: RESOLVE DOUBT REPORT
  CA reviews all flagged items:
    Each shows: line item, AI's best guess, confidence %, reason, alternatives
    CA picks the correct CMA field for each
    → Same correction flow as Step 8

Step 10: GENERATE EXCEL
  After all items approved/corrected:
    System opens CMA.xlsm template with openpyxl (keep_vba=True)
    Fills INPUT SHEET:
      - Header info (client name, years, nature, auditor)
      - P&L data in correct rows (22-109) and year columns (B, C, D)
      - Balance Sheet data in correct rows (116-262) and year columns
    Fills TL Sheet:
      - Monthly loan repayment data
    Saves as client_name_CMA_2024.xlsm
    → File saved to Supabase Storage
    → Audit trail entry: "Excel generated"

Step 11: DOWNLOAD & REVIEW
  CA downloads the .xlsm file
  Opens in Excel — macros auto-populate all other sheets
  CA does final human review
  Submits to bank
```

---

## 12. CMA EXCEL GENERATION — EXACT CELL MAPPING

### How the system writes to INPUT SHEET

The system must map each classified line item to an exact cell in the INPUT SHEET. The cell = (row, column).

**Column mapping by year:**
```python
YEAR_TO_COLUMN = {
    2023: 'B',
    2024: 'C',
    2025: 'D',
    2026: 'E',
    2027: 'F',
    2028: 'G',
    2029: 'H',
    2030: 'I',
    2031: 'J',
    2032: 'K',
    2033: 'L',
    2034: 'M',
}
```

**Row mapping by CMA field (P&L section):**
```python
PNL_FIELD_TO_ROW = {
    'Domestic Sales': 22,
    'Export Sales': 23,
    'Less Excise Duty and Cess': 25,
    'Dividends received from Mutual Funds': 29,
    'Interest Received': 30,
    'Profit on sale of fixed assets / Investments': 31,
    'Gain on Exchange Fluctuations': 32,
    'Extraordinary income': 33,
    'Others (Non-Operating Income)': 34,
    'Raw Materials Consumed (Imported)': 41,
    'Raw Materials Consumed (Indigenous)': 42,
    'Stores and spares consumed (Imported)': 43,
    'Stores and spares consumed (Indigenous)': 44,
    'Wages': 45,
    'Processing / Job Work Charges': 46,
    'Freight and Transportation Charges': 47,
    'Power, Coal, Fuel and Water': 48,
    'Others (Manufacturing)': 49,
    'Repairs & Maintenance (Manufacturing)': 50,
    'Security Service Charges': 51,
    'Stock in process Opening Balance': 53,
    'Stock in process Closing Balance': 54,
    'Depreciation (Manufacturing)': 56,
    'Finished Goods Opening Balance': 58,
    'Finished Goods Closing Balance': 59,
    'Depreciation (CMA)': 63,
    'Other Manufacturing Exp (CMA)': 64,
    'Salary and staff expenses': 67,
    'Rent, Rates and Taxes': 68,
    'Bad Debts': 69,
    'Advertisements and Sales Promotions': 70,
    'Others (Admin)': 71,
    'Repairs & Maintenance (Admin)': 72,
    'Audit Fees & Directors Remuneration': 73,
    'Miscellaneous Expenses written off': 75,
    'Deferred Revenue Expenditures': 76,
    'Other Amortisations': 77,
    'Interest on Fixed Loans / Term loans': 83,
    'Interest on Working capital loans': 84,
    'Bank Charges': 85,
    'Loss on sale of fixed assets / Investments': 89,
    'Sundry Balances Written off': 90,
    'Loss on Exchange Fluctuations': 91,
    'Extraordinary losses': 92,
    'Others (Non-Operating Expenses)': 93,
    'Income Tax provision': 99,
    'Deferred Tax Liability (P&L)': 100,
    'Deferred Tax Asset (P&L)': 101,
    'Brought forward from previous year': 106,
    'Dividend': 107,
    'Other Appropriation of profit': 108,
}
```

**Row mapping by CMA field (Balance Sheet section):**
```python
BS_FIELD_TO_ROW = {
    'Issued, Subscribed and Paid up': 116,
    'Share Application Money': 117,
    'General Reserve': 121,
    'Balance transferred from profit and loss a/c': 122,
    'Share Premium A/c': 123,
    'Revaluation Reserve': 124,
    'Other Reserve': 125,
    'Working Capital Bank Finance - Bank 1': 131,
    'Working Capital Bank Finance - Bank 2': 132,
    'Term Loan Repayable in next one year': 136,
    'Term Loan Balance Repayable after one year': 137,
    'Debentures Repayable in next one year': 140,
    'Debentures Balance Repayable after one year': 141,
    'Preference Shares Repayable in next one year': 144,
    'Preference Shares Balance Repayable after one year': 145,
    'Other Debts Repayable in Next One year': 148,
    'Balance Other Debts': 149,
    'Unsecured Loans - Quasi Equity': 152,
    'Unsecured Loans - Long Term Debt': 153,
    'Unsecured Loans - Short Term Debt': 154,
    'Deferred tax liability (BS)': 159,
    'Gross Block': 162,
    'Less Accumulated Depreciation': 163,
    'Capital Work in Progress': 165,
    'Patents / goodwill / copyrights etc': 169,
    'Misc Expenditure (to the extent not w/o)': 170,
    'Deferred Tax Asset (BS)': 171,
    'Other Intangible assets': 172,
    'Additions to Fixed Assets': 175,
    'Sale of Fixed assets WDV': 176,
    'Profit on sale of Fixed assets (BS)': 177,
    'Loss on sale of Fixed assets (BS)': 178,
    'Investment in Govt. Securities (Current)': 182,
    'Investment in Govt. Securities (Non Current)': 183,
    'Other current investments': 185,
    'Other non current investments': 186,
    'Investment in group companies / subsidiaries': 188,
    'Raw Material Imported': 193,
    'Raw Material Indigenous': 194,
    'Stores and Spares Imported': 197,
    'Stores and Spares Indigenous': 198,
    'Stocks-in-process': 200,
    'Finished Goods': 201,
    'Domestic Receivables': 206,
    'Export Receivables': 207,
    'Debtors more than 6 months': 208,
    'Cash on Hand': 212,
    'Bank Balances': 213,
    'Fixed Deposit under lien': 214,
    'Other Fixed Deposits': 215,
    'Advances recoverable in cash or in kind': 219,
    'Advances to suppliers of raw materials': 220,
    'Advance Income Tax': 221,
    'Prepaid Expenses': 222,
    'Other Advances / current asset': 223,
    'Advances to group / subsidiaries companies': 224,
    'Exposure in group companies - Investments': 229,
    'Exposure in group companies - Advances': 230,
    'Debtors more than six months (Non-Current)': 232,
    'Investments (Non-Current)': 233,
    'Fixed Deposits (Non Current)': 234,
    'Dues from directors / partners / promoters': 235,
    'Advances to suppliers of capital goods': 236,
    'Security deposits with government departments': 237,
    'Other non current assets': 238,
    'Sundry Creditors for goods': 242,
    'Advance received from customers': 243,
    'Provision for Taxation': 244,
    'Dividend payable': 245,
    'Other statutory liabilities (due within 1 year)': 246,
    'Interest Accrued but not due': 247,
    'Interest Accrued and due': 248,
    'Creditors for Expenses': 249,
    'Other current liabilities': 250,
    'Arrears of cumulative dividends': 254,
    'Gratuity liability not provided for': 255,
    'Disputed excise / customs / tax liabilities': 256,
    'Bank guarantee / Letter of credit outstanding': 257,
    'Other contingent liabilities': 258,
}
```

### How the system writes to TL Sheet

```python
# TL Sheet structure
# Row 4: Interest rates
# Row 5: Opening balances (date in A5)
# Rows 6-53: Monthly data

TL_COLUMNS = {
    'term_loan_ob': 'B',
    'term_loan_payment': 'C',
    'term_loan_cb': 'D',
    'term_loan_interest': 'E',
    'wc_loan_ob': 'F',
    'wc_loan_additions': 'G',
    'wc_loan_cb': 'H',
    'wc_loan_interest': 'I',
}
# Rows 6 onwards = monthly from April 2025
# The system maps each month's data to the corresponding row
```

---

## 13. PROJECT STRUCTURE

```
cma-automation/
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    — FastAPI app entry point
│   │   ├── config.py                  — Environment variables, settings
│   │   ├── dependencies.py            — Shared dependencies (Supabase client, etc.)
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                — Auth endpoints
│   │   │   ├── clients.py             — Client CRUD endpoints
│   │   │   ├── documents.py           — Document upload/management
│   │   │   ├── extraction.py          — Extraction trigger + verification
│   │   │   ├── classification.py      — Classification + review + doubt report
│   │   │   ├── cma_reports.py         — CMA report management + Excel generation
│   │   │   ├── reference.py           — Reference data (CMA fields)
│   │   │   ├── rollover.py            — Annual rollover endpoints
│   │   │   └── tasks.py               — Async task status endpoints
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── extraction/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── excel_extractor.py    — openpyxl/xlrd extraction
│   │   │   │   ├── pdf_extractor.py      — pdfplumber extraction
│   │   │   │   ├── ocr_extractor.py      — surya-ocr for scanned PDFs
│   │   │   │   └── extractor_factory.py  — Routes to correct extractor by file type
│   │   │   │
│   │   │   ├── classification/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── fuzzy_matcher.py      — rapidfuzz Tier 1 matching
│   │   │   │   ├── ai_classifier.py      — Claude Haiku/Sonnet Tier 2/3
│   │   │   │   ├── learning_system.py    — Query learned_mappings, update on corrections
│   │   │   │   └── pipeline.py           — Orchestrates 3-tier classification
│   │   │   │
│   │   │   ├── excel_generator.py        — Generates CMA .xlsm output
│   │   │   ├── audit_service.py          — Logs actions to cma_report_history
│   │   │   ├── rollover_service.py       — Annual rollover logic
│   │   │   └── conversion_service.py     — Provisional → Audited conversion
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py                — Pydantic request/response schemas
│   │   │   └── ai_schemas.py             — Pydantic schemas for Claude messages.parse()
│   │   │
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── worker.py                 — ARQ worker setup
│   │   │   ├── extraction_tasks.py       — Background extraction task
│   │   │   └── classification_tasks.py   — Background classification task
│   │   │
│   │   ├── mappings/
│   │   │   ├── __init__.py
│   │   │   ├── cma_field_rows.py         — PNL_FIELD_TO_ROW + BS_FIELD_TO_ROW dicts
│   │   │   └── year_columns.py           — YEAR_TO_COLUMN dict
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_helpers.py           — File type detection, temp file handling
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_extraction.py
│       ├── test_classification.py
│       ├── test_fuzzy_matcher.py
│       ├── test_excel_generator.py
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                — Root layout with auth provider
│   │   │   ├── page.tsx                  — Dashboard
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   ├── clients/
│   │   │   │   ├── page.tsx              — Client list
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx          — Create client
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx          — Client detail
│   │   │   │       ├── upload/
│   │   │   │       │   └── page.tsx      — Upload documents
│   │   │   │       ├── cma/
│   │   │   │       │   └── new/
│   │   │   │       │       └── page.tsx  — Start new CMA
│   │   │   │       └── rollover/
│   │   │   │           └── page.tsx      — Annual rollover
│   │   │   ├── cma/
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx          — CMA overview + confidence dashboard
│   │   │   │       ├── verify/
│   │   │   │       │   └── page.tsx      — Extraction verification
│   │   │   │       ├── review/
│   │   │   │       │   └── page.tsx      — Side-by-side review
│   │   │   │       ├── doubts/
│   │   │   │       │   └── page.tsx      — Doubt report
│   │   │   │       ├── audit-trail/
│   │   │   │       │   └── page.tsx      — Change log
│   │   │   │       └── convert/
│   │   │   │           └── page.tsx      — Provisional → Audited
│   │   │   └── settings/
│   │   │       └── page.tsx              — Admin settings
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                       — shadcn/ui components (Button, Input, etc.)
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── AuthGuard.tsx
│   │   │   ├── clients/
│   │   │   │   ├── ClientCard.tsx
│   │   │   │   ├── ClientForm.tsx
│   │   │   │   └── ClientSearch.tsx
│   │   │   ├── documents/
│   │   │   │   ├── DocumentUploader.tsx
│   │   │   │   └── DocumentList.tsx
│   │   │   ├── extraction/
│   │   │   │   ├── ExtractionVerifier.tsx
│   │   │   │   └── LineItemEditor.tsx
│   │   │   ├── classification/
│   │   │   │   ├── ClassificationReview.tsx
│   │   │   │   ├── DoubtReport.tsx
│   │   │   │   ├── CMAFieldSelector.tsx
│   │   │   │   └── ConfidenceDashboard.tsx
│   │   │   ├── cma/
│   │   │   │   ├── CMAOverview.tsx
│   │   │   │   ├── ConversionDiff.tsx
│   │   │   │   └── RolloverWizard.tsx
│   │   │   └── common/
│   │   │       ├── ProgressTracker.tsx
│   │   │       ├── AuditTrail.tsx
│   │   │       └── ConfirmDialog.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── supabase/
│   │   │   │   ├── client.ts             — Browser Supabase client
│   │   │   │   └── server.ts             — Server Supabase client
│   │   │   ├── api.ts                    — API client (fetch wrapper for FastAPI)
│   │   │   └── utils.ts                  — Shared utilities
│   │   │
│   │   └── types/
│   │       └── index.ts                  — TypeScript type definitions
│   │
│   └── public/
│       └── ...
│
├── DOCS/
│   ├── CMA classification.xls            — Reference mapping file (384 items)
│   └── CMA.xlsm                          — CMA template with macros
│
└── scripts/
    ├── import_reference_data.py           — One-time script: imports CMA classification.xls
    │                                        into cma_reference_mappings table
    └── seed_test_data.py                  — Creates test client with sample data
```

---

## 14. BUILD PHASES (Suggested Order)

### Phase 1: Foundation
- Docker setup (docker-compose with FastAPI + Next.js + Redis)
- Supabase project setup (DB, Auth, Storage)
- Database migration (all tables + indexes + RLS)
- FastAPI project scaffold with health check endpoint
- Next.js project scaffold with Tailwind + shadcn/ui
- Auth flow (register, login, logout, protected routes)
- Import CMA Classification Excel into DB (reference mappings)

### Phase 2: Client Management
- Client CRUD API endpoints
- Client list page with search
- Create/edit client form
- Client detail page

### Phase 3: Document Upload & Extraction
- File upload API (Supabase Storage)
- Document upload UI (drag & drop, metadata selection)
- Excel extractor service (openpyxl/xlrd)
- PDF extractor service (pdfplumber)
- OCR extractor service (surya-ocr)
- ARQ worker for background extraction
- Extraction progress tracking (API + UI)
- Extraction verification screen (mandatory confirmation step)

### Phase 4: Classification Engine
- Import reference mappings from CMA Classification Excel
- Fuzzy matcher service (rapidfuzz against reference + learned mappings)
- AI classifier service (Claude Haiku via messages.parse())
- 3-tier classification pipeline
- ARQ worker for background classification
- Doubt report generation

### Phase 5: Review Interface
- Confidence dashboard (summary stats + charts)
- Side-by-side review UI (TanStack Table + react-resizable-panels)
- CMA field selector dropdown (searchable)
- Approve / correct / flag per item
- Bulk approve high-confidence items
- Doubt report page (CA resolves uncertain items)
- Learning system (corrections → learned_mappings table)
- Audit trail logging

### Phase 6: Excel Generation
- CMA Excel generator service (openpyxl with keep_vba=True)
- Exact cell mapping (field → row/column in INPUT SHEET)
- TL sheet population
- Header info population
- Download endpoint
- Download UI

### Phase 7: Advanced Features
- Provisional to Audited conversion (diff view + confirm)
- Annual rollover wizard (guided process)
- User management (admin creates employees)
- Settings page

### Phase 8: Polish & Testing
- Error handling across all endpoints
- Loading states and progress indicators
- Mobile responsiveness (basic — not primary but should work)
- End-to-end testing with real CMA documents
- Docker production builds (multi-stage Dockerfiles)

---

## 15. CRITICAL CONSTRAINTS FOR THE PLANNER

1. **NEVER skip the verification step.** Between extraction and classification, the user MUST confirm extracted data. This is the #1 safety requirement.

2. **The CMA Excel template must preserve macros.** Always use `keep_vba=True` when loading and saving .xlsm files. Always save as .xlsm, never .xlsx.

3. **Classification must use the 3-tier pipeline.** Don't send everything to the AI — most items match the reference table via fuzzy matching (free). AI is only for ambiguous items.

4. **Industry type matters for classification.** The same line item can map differently for manufacturing vs service vs trading. Industry type must be available to the classifier.

5. **Doubt items must be explicitly flagged.** The system must NEVER silently guess on uncertain classifications. When confidence is below threshold, it goes to the doubt report.

6. **The learned_mappings table is checked BEFORE the reference table.** Past corrections take priority because they represent the CA's actual decisions for this firm's clients.

7. **All actions must be audit-logged.** Every extraction, classification, correction, approval, and generation event must be logged to cma_report_history.

8. **Docker must work for local development with hot reload.** The developer (non-coder) needs `docker compose up` to start everything. No manual setup steps.

9. **The UI must be professional.** Use shadcn/ui components consistently. Clean, modern design. This may become a product.

10. **V1 has NO projections.** Do not build anything related to future year projections, Details Sheet interaction, or projection calculations.

---

## 16. ENVIRONMENT VARIABLES

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Redis (for ARQ task queue)
REDIS_URL=redis://redis:6379

# App
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development

# Next.js
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 17. KEY DECISIONS SUMMARY

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend language | Python | Best PDF/Excel ecosystem |
| Backend framework | FastAPI | Async-first, modern, fast |
| Frontend | Next.js 15 App Router | Professional UI, SSR, best hosting |
| Database | Supabase (PostgreSQL) | Free tier, Auth, Storage, RLS |
| File storage | Supabase Storage | Same platform, simple |
| Auth | Supabase Auth | Built-in, role management |
| Excel reading | openpyxl + xlrd | Perfect accuracy |
| Excel writing | openpyxl (keep_vba=True) | Only option that preserves macros |
| PDF extraction | pdfplumber | Best for text-based PDFs |
| OCR | surya-ocr | 2x more accurate than pytesseract |
| Fuzzy matching | rapidfuzz | 2-4x faster than fuzzywuzzy |
| AI classification | Claude Haiku via messages.parse() | Cheapest, structured output |
| AI escalation | Claude Sonnet (only for truly ambiguous) | Higher reasoning when needed |
| Task queue | ARQ + Redis | Async-native, FastAPI fit |
| UI components | shadcn/ui + TanStack Table | Professional, customizable |
| Review layout | react-resizable-panels | Split pane for side-by-side |
| Charts | recharts | Confidence dashboard |
| Containerization | Docker + docker-compose | Local = production parity |
| Hosting (backend) | Railway Mumbai | Docker-native, Indian region |
| Hosting (frontend) | Vercel | Best Next.js hosting |
| Estimated cost | ₹50-600/month | Mostly free tiers |
