-- Fix C1: Populate cma_input_row for all reference mapping rows
-- Updates by cma_form_item (the actual column) not cma_field_name
-- Run in Supabase SQL Editor → New query → Run
-- Expected final check: "still_null = 0" (or close to 0 for non-mappable rows)

-- ── P&L Section ──────────────────────────────────────────────────────────────

-- Sales
UPDATE cma_reference_mappings SET cma_input_row = 22  WHERE cma_form_item = 'Item 1 (i) : Domestic sales';
UPDATE cma_reference_mappings SET cma_input_row = 22  WHERE cma_form_item = 'Item 1 : Gross Sales';
UPDATE cma_reference_mappings SET cma_input_row = 22  WHERE cma_form_item = 'Item 1 : Domestic / Export sales as applicable';
UPDATE cma_reference_mappings SET cma_input_row = 23  WHERE cma_form_item = 'Item 1 (ii) : Export sales';
UPDATE cma_reference_mappings SET cma_input_row = 25  WHERE cma_form_item = 'Item 2 : Less Excise duty';

-- Raw Materials / Cost of Production
UPDATE cma_reference_mappings SET cma_input_row = 41  WHERE cma_form_item = 'Item 5 (i) (a) : RM - Imported';
UPDATE cma_reference_mappings SET cma_input_row = 42  WHERE cma_form_item = 'Item 5 (i) (b) : RM - Indigenous';
UPDATE cma_reference_mappings SET cma_input_row = 42  WHERE cma_form_item = 'Item 5 (i) (b) : RM – Indigenous';
UPDATE cma_reference_mappings SET cma_input_row = 42  WHERE cma_form_item = 'Item 5 (i) (a) or (b) : RM – Indigenous / Imported';
UPDATE cma_reference_mappings SET cma_input_row = 44  WHERE cma_form_item = 'Item 5 (ii) (b) : Other Spares - Indegineous';
UPDATE cma_reference_mappings SET cma_input_row = 48  WHERE cma_form_item = 'Item 5 (iii) : Power & Fuel';
UPDATE cma_reference_mappings SET cma_input_row = 45  WHERE cma_form_item = 'Item 5 (iv) : Direct Labour (factory wages & Salaries)';
UPDATE cma_reference_mappings SET cma_input_row = 49  WHERE cma_form_item = 'Item 5 (v) : Other manufacturing expenses';
UPDATE cma_reference_mappings SET cma_input_row = 56  WHERE cma_form_item = 'Item 5 (vi) : Depreciation';
UPDATE cma_reference_mappings SET cma_input_row = 99  WHERE cma_form_item = 'Item 5: Provision for taxation';

-- SG&A
UPDATE cma_reference_mappings SET cma_input_row = 71  WHERE cma_form_item = 'Item 6 : Selling, General & Administrative Expenses';

-- Interest & Finance
UPDATE cma_reference_mappings SET cma_input_row = 84  WHERE cma_form_item = 'Item 9 : Bank Interest';
UPDATE cma_reference_mappings SET cma_input_row = 83  WHERE cma_form_item = 'Item 9 : Interest';

-- Non-Operating
UPDATE cma_reference_mappings SET cma_input_row = 34  WHERE cma_form_item = 'Item 11 (i) : Other non-operating income';
UPDATE cma_reference_mappings SET cma_input_row = 93  WHERE cma_form_item = 'Item 11 (ii) : Other non-operating expenses';

-- Tax & Appropriation
UPDATE cma_reference_mappings SET cma_input_row = 99  WHERE cma_form_item = 'Item 13 : Provision for Taxes';
UPDATE cma_reference_mappings SET cma_input_row = 107 WHERE cma_form_item = 'Item 15 (a) : Equity Dividend paid amount';

-- ── Balance Sheet: Current Liabilities ───────────────────────────────────────

UPDATE cma_reference_mappings SET cma_input_row = 131 WHERE cma_form_item = 'Item 1: Short term borrowings from banks';
UPDATE cma_reference_mappings SET cma_input_row = 131 WHERE cma_form_item = 'Item 1 (i) / (ii) : Short term borrowings from banks - of which BD / BP (Also to be included in (iii) )';
UPDATE cma_reference_mappings SET cma_input_row = 131 WHERE cma_form_item = 'Item 1: Short term borrowings from banks (Being excess borrowings placed on repayment basis)';
UPDATE cma_reference_mappings SET cma_input_row = 154 WHERE cma_form_item = 'Item 2: Short term borrowings from others';
UPDATE cma_reference_mappings SET cma_input_row = 242 WHERE cma_form_item = 'Item 3: Sundry creditors (Trade)';
UPDATE cma_reference_mappings SET cma_input_row = 243 WHERE cma_form_item = 'Item 4: Advance payment from customers / deposits from dealers';
UPDATE cma_reference_mappings SET cma_input_row = 244 WHERE cma_form_item = 'Item 5: Provision for taxation';
UPDATE cma_reference_mappings SET cma_input_row = 245 WHERE cma_form_item = 'Item 6: Dividend payable';
UPDATE cma_reference_mappings SET cma_input_row = 246 WHERE cma_form_item = 'Item 7: Other statutory liabilities';
UPDATE cma_reference_mappings SET cma_input_row = 136 WHERE cma_form_item = 'Item 8: Deposits/ installments of term loans / DPGs / Debentures etc. repayable within 1 year';
UPDATE cma_reference_mappings SET cma_input_row = 250 WHERE cma_form_item = 'Item 9: Other current liabilities';

-- ── Balance Sheet: Term Liabilities ──────────────────────────────────────────

UPDATE cma_reference_mappings SET cma_input_row = 140 WHERE cma_form_item = 'Item 11: Debentures';
UPDATE cma_reference_mappings SET cma_input_row = 145 WHERE cma_form_item = 'Item 12: Preference shares (redeemable after 1 year)';
UPDATE cma_reference_mappings SET cma_input_row = 137 WHERE cma_form_item = 'Item 13: Term Loans';
UPDATE cma_reference_mappings SET cma_input_row = 149 WHERE cma_form_item = 'Item 14: Deferred payment credits';
UPDATE cma_reference_mappings SET cma_input_row = 215 WHERE cma_form_item = 'Item 15: Term deposits';
UPDATE cma_reference_mappings SET cma_input_row = 153 WHERE cma_form_item = 'Item 16: Other term liabilities';

-- ── Balance Sheet: Networth ───────────────────────────────────────────────────

UPDATE cma_reference_mappings SET cma_input_row = 116 WHERE cma_form_item = 'Item 19: Ordinary Share Capital';
UPDATE cma_reference_mappings SET cma_input_row = 121 WHERE cma_form_item = 'Item 20: General Reserve';
UPDATE cma_reference_mappings SET cma_input_row = 124 WHERE cma_form_item = 'Item 21: Revaluation Reserve';
UPDATE cma_reference_mappings SET cma_input_row = 125 WHERE cma_form_item = 'Item 22: Other Reserves';
UPDATE cma_reference_mappings SET cma_input_row = 125 WHERE cma_form_item = 'Item 23: Capital Redemption Reserve';
UPDATE cma_reference_mappings SET cma_input_row = 125 WHERE cma_form_item = 'Item 23: Net worth - Others';
UPDATE cma_reference_mappings SET cma_input_row = 125 WHERE cma_form_item = 'Item 23: Networth – Others';
UPDATE cma_reference_mappings SET cma_input_row = 125 WHERE cma_form_item = 'Item 23: Others';
UPDATE cma_reference_mappings SET cma_input_row = 123 WHERE cma_form_item = 'Item 23: Share Premium';
UPDATE cma_reference_mappings SET cma_input_row = 122 WHERE cma_form_item = 'Item 23: Surplus / Deficit in Profit & Loss A/c';
UPDATE cma_reference_mappings SET cma_input_row = 122 WHERE cma_form_item = 'Item 23: Surplus / deficit in Profit & Loss A/c (Put figure with – ve sign)';

-- ── Balance Sheet: Current Assets ────────────────────────────────────────────

UPDATE cma_reference_mappings SET cma_input_row = 213 WHERE cma_form_item = 'Item 26: Cash & bank balances';
UPDATE cma_reference_mappings SET cma_input_row = 183 WHERE cma_form_item = 'Item 27 (i) : Investments – Gvt. And other trustee securities';
UPDATE cma_reference_mappings SET cma_input_row = 215 WHERE cma_form_item = 'Item 27 (ii): Investments (other than long term) - Fixed Deposits with banks';
UPDATE cma_reference_mappings SET cma_input_row = 206 WHERE cma_form_item = 'Item 28: Receivables';
UPDATE cma_reference_mappings SET cma_input_row = 194 WHERE cma_form_item = 'Item 30 (i): Inventory - Raw Materials';
UPDATE cma_reference_mappings SET cma_input_row = 200 WHERE cma_form_item = 'Item 30 (ii): Inventory - stocks-in-progress';
UPDATE cma_reference_mappings SET cma_input_row = 201 WHERE cma_form_item = 'Item 30 (iii): Inventory - Finished goods';
UPDATE cma_reference_mappings SET cma_input_row = 194 WHERE cma_form_item = 'Item 30: Inventory';
UPDATE cma_reference_mappings SET cma_input_row = 220 WHERE cma_form_item = 'Item 31: Advance to supplier of raw material and stores / spares';
UPDATE cma_reference_mappings SET cma_input_row = 221 WHERE cma_form_item = 'Item 32: Advance payment of taxes';
UPDATE cma_reference_mappings SET cma_input_row = 219 WHERE cma_form_item = 'Item 33 (c): Other current assets - Loans & advances';
UPDATE cma_reference_mappings SET cma_input_row = 223 WHERE cma_form_item = 'Item 33: Other current assets';

-- ── Balance Sheet: Fixed Assets ───────────────────────────────────────────────

UPDATE cma_reference_mappings SET cma_input_row = 162 WHERE cma_form_item = 'Item 35: Gross block under fixed assets';
UPDATE cma_reference_mappings SET cma_input_row = 162 WHERE cma_form_item = 'Item 35: Gross block under Fixed Assets';
UPDATE cma_reference_mappings SET cma_input_row = 163 WHERE cma_form_item = 'Item 36: Depreciation to date';
UPDATE cma_reference_mappings SET cma_input_row = 169 WHERE cma_form_item = 'Item 42: Intangible Assets';

-- ── Balance Sheet: Non-Current Assets ────────────────────────────────────────

UPDATE cma_reference_mappings SET cma_input_row = 230 WHERE cma_form_item = 'Item 38 (i) (b) : Investments / book debts / advances / deposits which are non-current - Loans to subsidiaries';
UPDATE cma_reference_mappings SET cma_input_row = 236 WHERE cma_form_item = 'Item 38 (ii): Investments / book debts / advances / deposits which are non-current - Advance to supplier of capital goods / contractors';
UPDATE cma_reference_mappings SET cma_input_row = 233 WHERE cma_form_item = 'Item 38 (iv) (a) : Investments / book debts / advances / deposits which are non-current';
UPDATE cma_reference_mappings SET cma_input_row = 238 WHERE cma_form_item = 'Item 38 (iv) (c): Investments / book debts / advances / deposits which are non-current';
UPDATE cma_reference_mappings SET cma_input_row = 233 WHERE cma_form_item = 'Item 38: Investments / book debts / advances / deposits which are non-current';
UPDATE cma_reference_mappings SET cma_input_row = 198 WHERE cma_form_item = 'Item 39: Non-consumable stores and spares';
UPDATE cma_reference_mappings SET cma_input_row = 238 WHERE cma_form_item = 'Item 40: Other non-current assets including dues from directors';

-- ── Verify ────────────────────────────────────────────────────────────────────
-- Rows still NULL are non-mappable items (deduction instructions, additional info)
-- Expected: ~8-10 rows remaining NULL (the "Deduct from..." and "Not appear in..." rows)
SELECT COUNT(*) as still_null FROM cma_reference_mappings WHERE cma_input_row IS NULL;

-- Sanity check: how many rows were updated
SELECT COUNT(*) as rows_with_row_number FROM cma_reference_mappings WHERE cma_input_row IS NOT NULL;
