# CMA Classification Rules — V1
**For review by:** Ashutosh / CA Firm
**Source:** Derived from Agent 5 test run on Mehta Computers FY2024
**Status:** Implemented in `rule_engine.py` — awaiting your verification

These rules run before the AI even sees the item (Tier 0). They are pattern-based
and always give the same answer for the same input. Each rule below has:
- What the rule does
- Why it exists (the mistake it fixes)
- A real example from Mehta Computers' books
- How to tell me if it's wrong

---

## RULE A-001 / A-002 — GST-Coded Purchase Entries (HIGH PRIORITY)

**Applies to:** Trading industry only

**Pattern it catches:**
- `Purchase @ 18% (Local)`
- `Purchase @ 5% (Inter-State)`
- `Purchase @ 12% IGST`
- `Purchases @ 28%`

**Classification:** Raw Materials Consumed (Indigenous) → Row 42

**Why this rule exists:**
When you buy goods for resale in a trading firm, accountants often write the entry
as "Purchase @ 18%" (the GST rate on the invoice). The app was seeing "Purchase @ 18%"
and not recognising it as a purchase — so it was sending it to doubt.

In a trading firm, *any* GST-coded purchase = goods bought for resale = Raw Materials.

**Real example from Mehta Computers FY2024:**
```
Source text:   "Purchase @ 18% (Local)"
Amount:        ₹1,74,12,563
Correct field: Raw Materials Consumed (Indigenous)  [Row 42]
Old result:    DOUBT (AI unsure)
New result:    Auto-classified, confidence 0.97  ✓
```

**When this rule would be WRONG:**
If a firm buys capital equipment and the accountant writes "Purchase @ 18% (Fixed Asset)"
— but in practice accountants never write it that way; capital items go in a separate ledger.

**Verify:** Do you agree all "Purchase @ N%" entries in a trading firm = Raw Materials?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE B-001 — Bank Interest on Income Side

**Pattern it catches:**
- Description: `Bank Interest`
- Section: income / receipts / revenue / credit side

**Classification:** Interest Received → Row 30

**Why this rule exists:**
"Bank Interest" appears on BOTH sides of the accounts:
- On the expense side → Bank Charges (row 85)
- On the income side → Interest Received (row 30) ← this rule fixes that

The old AI was sometimes classifying income-side Bank Interest as Bank Charges.

**Real example:**
```
Source text:   "Bank Interest"
Section:       "Income from Operations"
Amount:        ₹4,250
Correct field: Interest Received  [Row 30]
Old result:    Bank Charges (WRONG)
New result:    Interest Received  ✓
```

**Verify:** Do you agree "Bank Interest" on the income side = Interest Received?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE B-002 — ALL CAPS Vendor Names as Sundry Creditors

**Applies to:** Trading industry, liabilities section of Balance Sheet

**Pattern it catches:**
- Description is a company name in ALL CAPS (e.g. `UTTAM MARKETING`, `RELIANCE INFRA`)
- Located in liability / creditor section of Balance Sheet

**Classification:** Sundry Creditors for goods → Row 242

**Why this rule exists:**
In Tally and other accounting software, supplier names are often entered in ALL CAPS.
When these appear in the Balance Sheet under creditors, the AI was sometimes
misclassifying "UTTAM MARKETING" as an advertising expense because of the word "MARKETING".

**Real example from Mehta Computers FY2024:**
```
Source text:   "UTTAM MARKETING"
Section:       "Creditors" (Balance Sheet)
Correct field: Sundry Creditors for goods  [Row 242]
Old result:    Advertisements and Sales Promotions (WRONG)
New result:    Sundry Creditors for goods  ✓
```

**Note:** This rule only fires if the text is ALL CAPS AND in a liability section.
Normal mixed-case "Uttam Marketing" will still go to the AI.

**Verify:** Do you agree ALL-CAPS company names in the creditors section = Sundry Creditors?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE B-003 — Unqualified "Interest Paid" in Trading Firms

**Applies to:** Trading industry only

**Pattern it catches:**
- Description is exactly `Interest Paid` or `Interest` (no loan type specified)
- Industry: Trading

**Classification:** Interest on Working capital loans → Row 84

**Why this rule exists:**
Trading firms primarily borrow through cash credit / overdraft (working capital facilities),
not term loans. When an accountant just writes "Interest Paid" without specifying the loan type,
in a trading firm it almost always refers to working capital interest.

**Real example:**
```
Source text:   "Interest Paid"
Industry:      Trading
Amount:        ₹84,000
Correct field: Interest on Working capital loans  [Row 84]
Old result:    DOUBT (AI asked: "is this term loan or working capital?")
New result:    Interest on Working capital loans  ✓
```

**When this rule would be WRONG:**
If a trading firm has a term loan and the accountant just writes "Interest Paid".
→ In that case, you should correct it manually in the verification screen.

**Verify:** In your CA firm's trading clients, is most interest on working capital?
☐ Yes, correct   ☐ No, it's usually term loan interest: _______________________

---

## RULE C-001 — Motor Vehicles → Always Fixed Asset (ABSOLUTE RULE)

**Applies to:** All industries

**Pattern it catches:**
- `Motor Vehicle`, `Car`, `Truck`, `Lorry`, `Two Wheeler`, `Motorcycle`, `Scooter`,
  `Tempo`, `Van`, `Auto Rickshaw`, `Vehicle`

**Classification:** Gross Block → Row 162

**Why this rule exists:**
Vehicles are always fixed assets regardless of industry. There is no scenario where
"Motor Vehicle" should go anywhere except Gross Block. The old AI occasionally doubted
vehicles in service firms or put them under "Others (Manufacturing)".

**Real example:**
```
Source text:   "Motor Vehicle Loan A/c"  (Balance Sheet, Assets side)
Correct field: Gross Block  [Row 162]
Old result:    DOUBT
New result:    Gross Block, confidence 0.97  ✓
```

**Verify:** Do you agree vehicles always go to Gross Block (Fixed Assets)?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE C-002 — Electronics: Capitalize ≥ ₹5,000 / Expense < ₹5,000

**Pattern it catches:**
- `Mobile`, `Cell Phone`, `Laptop`, `Computer`, `Desktop`, `Tablet`, `Printer`,
  `Scanner`, `Projector`, `UPS`, `Server`

**Classification:**
- Amount ≥ ₹5,000 → Gross Block (Row 162) — capitalize as fixed asset
- Amount < ₹5,000 → Others (Admin) (Row 71) — treat as revenue expense
- Amount unknown → goes to AI to decide

**Why this rule exists:**
Under Indian Income Tax rules, assets costing less than ₹5,000 can be fully expensed
in the year of purchase. Above ₹5,000 they must be capitalized. This is a very common
source of errors in CMA classification for IT companies and trading firms.

**Real example from Mehta Computers FY2024:**
```
Source text:   "Laptop Purchase"
Amount:        ₹45,000
Correct field: Gross Block  [Row 162]
Old result:    Others (Admin) (WRONG — treated as expense)
New result:    Gross Block  ✓

Source text:   "Mobile Accessories"
Amount:        ₹1,200
Correct field: Others (Admin)  [Row 71]
New result:    Others (Admin)  ✓
```

**Important note for your verification:**
The ₹5,000 threshold is the old Income Tax rule. The current threshold under Companies Act
is ₹10,000 for some categories. If your firm uses ₹10,000 as the threshold, let me know
and I'll update the rule.

**Verify:** Does your firm use ₹5,000 or a different threshold for capitalizing electronics?
☐ ₹5,000 is correct   ☐ We use ₹_______ as threshold

---

## RULE C-003 — Freight / Carriage in Trading Firms

**Applies to:** Trading industry only

**Pattern it catches:**
- `Carriage Inward`, `Carriage Outward`, `Carriage In`, `Carriage Out`
- `Packing and Forwarding`, `Packing Forwarding`
- `Freight Charges`, `Freight Inward`, `Freight Outward`
- `Loading Charges`, `Transportation Charges`

**Classification:** Freight and Transportation Charges → Row 47

**Why this rule exists:**
In manufacturing firms, freight is part of Cost of Production. In trading firms,
it's still Row 47 (Freight and Transportation Charges). The AI was sometimes
putting trading firm freight under "Others (Manufacturing)" which is wrong for
a trading firm that doesn't manufacture anything.

**Real example from Mehta Computers FY2024:**
```
Source text:   "Carriage Outward"
Industry:      Trading
Amount:        ₹23,450
Correct field: Freight and Transportation Charges  [Row 47]
Old result:    Others (Manufacturing) (technically row 49 — wrong for trading)
New result:    Freight and Transportation Charges  ✓
```

**Verify:** Do you agree freight/carriage in trading firms goes to Row 47?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE C-004 — Security Deposits / Caution Deposits

**Pattern it catches:**
- `Security Deposit`, `Telephone Deposit`, `Electricity Deposit`
- `GEM Caution Deposit`, `Caution Deposit`, `Earnest Money`

**Classification:** Security deposits with government departments → Row 237

**Why this rule exists:**
Security deposits (given to landlords, electricity boards, telephone companies, government)
are long-term non-current assets. The AI was sometimes classifying them as prepaid expenses
or advances, which is incorrect.

**Real example from Mehta Computers FY2024:**
```
Source text:   "Telephone Deposit"
Amount:        ₹5,000
Correct field: Security deposits with government departments  [Row 237]
Old result:    Prepaid Expenses (WRONG)
New result:    Security deposits with government departments  ✓
```

**Note:** GEM (Government e-Marketplace) caution deposits are increasingly common
for government supplier registrations. This rule handles those too.

**Verify:** Do you agree all deposits (telephone, electricity, GEM) go to Row 237?
☐ Yes, correct   ☐ Some deposits should go elsewhere: _______________________

---

## RULE D-001 — Purchase Returns (Netting Against Raw Materials)

**Applies to:** Trading industry only

**Pattern it catches:**
- `Less: Purchase Return`
- `Purchase Returns`
- `Return of Purchases`
- `Return on Purchases`

**Classification:** Raw Materials Consumed (Indigenous) → Row 42
*(The amount will be negative — it is deducted from total purchases)*

**Why this rule exists:**
When goods are returned to a supplier, the accountant records "Less: Purchase Return"
as a deduction from purchases. This should be netted against Raw Materials (Row 42),
not classified as a separate expense line or sent to doubt.

**Real example from Mehta Computers FY2024:**
```
Source text:   "Less : Purchase Return"
Amount:        -₹3,24,500  (negative — it's a return)
Correct field: Raw Materials Consumed (Indigenous)  [Row 42]
Old result:    DOUBT
New result:    Raw Materials Consumed (Indigenous), confidence 0.97  ✓
```

**Verify:** Do you agree purchase returns should net against Raw Materials?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE D-002 — Sales Returns (Netting Against Domestic Sales)

**Pattern it catches:**
- `Less: Sale Return`
- `Sales Returns`
- `Return of Sales`

**Classification:** Domestic Sales → Row 22
*(The amount will be negative — it is deducted from gross sales)*

**Why this rule exists:**
Sales returns reduce gross sales. They should net against Domestic Sales (Row 22),
not appear as a separate expense.

**Real example:**
```
Source text:   "Less : Sale Return"
Amount:        -₹12,600  (negative — it's a return)
Correct field: Domestic Sales  [Row 22]
Old result:    DOUBT
New result:    Domestic Sales, confidence 0.97  ✓
```

**Verify:** Do you agree sales returns should net against Domestic Sales?
☐ Yes, correct   ☐ No, exception: _______________________

---

## RULE SYS-001 — Database Row Numbers (Already Applied)

This is not a classification rule — it's the database fix that was applied on 2026-03-19.

**What was fixed:** All 369 rows in the CMA reference mapping table now have correct
Excel row numbers. Before this fix, Tier 1 fuzzy matching was returning 0% hit rate
because every row had `cma_input_row = NULL`.

**Impact:** Doubt rate expected to drop from 66% → under 20% for all future documents.

---

## How to give me feedback on these rules

After reviewing each rule, tell me one of the following:
1. **"Rule X is correct"** — I keep it as-is
2. **"Rule X is wrong, it should do Y"** — I update the rule
3. **"Rule X needs an exception: when Z, do W instead"** — I add a sub-condition
4. **"Rule X should also apply to manufacturing firms"** — I remove the industry filter

You can test any rule by uploading a document and checking if the classification screen
shows the expected result. The `classification_method` column will show `rule_A-001`,
`rule_C-001`, etc. so you can see exactly which rule fired.

---

## Testing material we still need

To make the rules more robust across different client types, the following documents
would be very valuable to test:

| What to bring | Why it helps |
|---------------|-------------|
| A **manufacturing firm's** P&L and Balance Sheet | Tests that C-001/C-002 (vehicle/electronics) work correctly for non-trading industries; verifies "Wages" vs "Salary" distinction |
| A **service firm** (CA firm, IT company, consultant) | Tests that there are no Raw Material rows, salary classification is correct |
| Any client with **property/real estate** on BS | Tests Gross Block, depreciation, lease rental classification |
| Any client with **bank loan schedule** (term loan details) | Tests TL Sheet pipeline (currently deferred) |
| A client with **GST input credit** entries on BS | Tests classification of "GST Input Credit" / "IGST Receivable" |
| **Scanned PDFs** (not digitally generated) | Tests OCR pipeline — currently surya-ocr is not installed in Docker |
| A client with **multiple years** already in Tally | Tests the rollover / year-copy feature |

The most impactful addition right now would be **one manufacturing firm** — it will
test about 40% of CMA fields that Mehta Computers (a trading firm) never uses.
