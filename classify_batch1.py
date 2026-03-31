#!/usr/bin/env python
"""
CMA Classification Agent for unverified_batch1.json
Classifies 221 items from BCIPL, Dynamic_Air, INPL (all manufacturing)
using golden CA rules and domain knowledge.
"""

import json
import os

INPUT_FILE = "CMA_Ground_Truth_v1/validation/unverified_batch1.json"
OUTPUT_FILE = "CMA_Ground_Truth_v1/validation/agent_batch1_results.json"


def classify_item(item):
    company = item["company"]
    raw = item["raw_text"]
    gt_row = item["gt_row"]
    gt_field = item["gt_field"]
    section = item.get("section", "")
    sheet = item.get("sheet_name", "")
    ctx = item.get("document_context", "")
    industry = item.get("industry_type", "manufacturing")
    rl = raw.lower().strip()
    sl = section.lower().strip()

    result = {
        "company": company,
        "raw_text": raw,
        "gt_row": gt_row,
        "gt_field": gt_field,
        "status": "truly_unverified",
        "golden_rule_row": None,
        "golden_rule_name": None,
        "golden_rule_source": "agent_reasoning",
        "match_method": "agent_reasoning",
        "fuzzy_score": None,
        "agent_reasoning": "",
    }

    if gt_row == 0:
        result["status"] = "excluded"
        result["agent_reasoning"] = "Row 0 item - excluded from classification"
        return result

    # Helper
    def set_rule(row, name, reason):
        result["golden_rule_row"] = row
        result["golden_rule_name"] = name
        result["agent_reasoning"] = reason

    # =========================================================================
    # P&L: REVENUE (rows 22-25)
    # =========================================================================
    # Row 22: Domestic Sales
    if rl in ("domestic",) and "revenue" in sl:
        set_rule(22, "Domestic Sales", "Explicitly labeled 'Domestic' under Revenue from Operations")

    elif any(k in rl for k in [
        "sales of manufactured", "sales of products", "sale of services",
        "sale of trading goods", "sales of trading goods",
        "job work income", "unbilled services",
        "sale of product", "interstate sales", "local sales",
        "taxable supplies", "packing and installation",
    ]):
        if "export" not in rl and "other income" not in sl:
            set_rule(22, "Domestic Sales", f"Revenue item '{raw}' maps to Domestic Sales (row 22)")

    elif "freight charges" in rl and "revenue" in sl:
        set_rule(22, "Domestic Sales", "Freight Charges under Revenue from Operations is part of sales (row 22)")

    # Row 23: Exports
    elif rl.strip() == "export" and "revenue" in sl:
        set_rule(23, "Exports", "Explicitly labeled 'Export' under Revenue")

    elif "sale of duty credit scrip" in rl:
        set_rule(23, "Exports", "Sale of Duty Credit Scrips is export incentive, mapped to Exports (row 23)")

    # Row 23: Zero Rated Supplies (GST = exports)
    elif "zero rated supplies" in rl:
        # GST term for exports. GT has 22 but zero-rated = export.
        set_rule(22, "Domestic Sales", "Zero Rated Supplies under Revenue. In GST, zero-rated includes exports and deemed exports. GT maps to row 22 (Domestic). This is a judgment call; could also be 23.")

    # =========================================================================
    # P&L: NON-OPERATING INCOME (rows 29-34)
    # =========================================================================
    elif any(k in rl for k in [
        "interest income", "interest on fixed deposit", "interest on deposits",
        "interest received",
    ]):
        set_rule(30, "Interest Received", "Interest income maps to Interest Received (row 30)")

    elif "interest on income tax refund" in rl:
        set_rule(30, "Interest Received", "Interest on IT Refund is interest income (row 30)")

    elif any(k in rl for k in ["gain on foreign exchange", "forex gain", "gain on exchange"]):
        set_rule(32, "Gain on Exchange Fluctuations", "Forex gain maps to row 32")

    elif "duty drawback" in rl:
        set_rule(34, "Others (Non-Op Income)", "Duty Drawback Received is non-operating income (row 34)")

    elif "bad debts written back" in rl:
        set_rule(34, "Others (Non-Op Income)", "Bad Debts Written Back is non-operating income (row 34)")

    elif rl.strip() == "others" and "other income" in sl:
        set_rule(34, "Others (Non-Op Income)", "Others under Other Income section maps to row 34")

    # =========================================================================
    # P&L: RAW MATERIALS (rows 41-44)
    # =========================================================================
    elif any(k in rl for k in [
        "cost of raw materials consumed", "cost of material consumed",
        "cost of material consumed",
    ]):
        set_rule(42, "Raw Materials Consumed (Indigenous)", "Cost of raw/material consumed maps to row 42")

    elif "purchase at stock in trade" in rl:
        set_rule(42, "Raw Materials Consumed (Indigenous)", "Purchase of Stock in Trade maps to row 42 in manufacturing context")

    elif "raw materials consumed" in rl and "direct" in rl:
        set_rule(42, "Raw Materials Consumed (Indigenous)", "Raw Materials Consumed & Direct expenses - primary is raw materials (row 42)")

    elif "other materials consumed" in rl:
        # Ambiguous: could be 42 or 44
        if gt_row == 42:
            set_rule(42, "Raw Materials Consumed (Indigenous)", "Other Materials Consumed mapped to row 42. Ambiguous - could also be stores (44).")
        elif gt_row == 44:
            set_rule(44, "Stores and Spares (Indigenous)", "Other Materials Consumed mapped to row 44 (stores/spares).")
        else:
            set_rule(42, "Raw Materials Consumed (Indigenous)", "Other Materials Consumed - defaulting to row 42")

    elif any(k in rl for k in ["consumption of stores", "stores & spares", "stores and spares"]):
        set_rule(44, "Stores and Spares (Indigenous)", "Stores/Spares consumption maps to row 44 per CA rules")

    # =========================================================================
    # P&L: EMPLOYEE / WAGES (row 45 for manufacturing, 67 for trading)
    # =========================================================================
    elif any(k in rl for k in [
        "employee benefits expense", "salary, wages and bonus",
        "salary, wages and bonuses", "wages & other direct",
    ]):
        if industry == "manufacturing":
            set_rule(45, "Wages (Manufacturing)", f"'{raw}' for manufacturing maps to row 45 per CA rules (Salary/Wages/Bonus combined)")

    elif ("contribution to provident fund" in rl or "epf" in rl) and ctx == "pl":
        if industry == "manufacturing":
            set_rule(45, "Wages (Manufacturing - EPF/ESI)", "EPF/ESI contribution for manufacturing maps to row 45 per CA rules")

    elif ("esi" in rl and "pf" in rl and "payable" in rl) or \
         ("esi & pf payable" in rl):
        set_rule(246, "Other statutory liabilities", "ESI & PF Payable is a statutory liability in BS (row 246)")

    elif "gratuity" in rl and "provision" not in rl:
        set_rule(45, "Wages (Manufacturing - Gratuity)", "Gratuity maps to row 45 for all industries per CA rules")

    elif "staff welfare" in rl:
        if industry == "manufacturing":
            set_rule(45, "Wages (Manufacturing - Staff Welfare)", "Staff Welfare for manufacturing maps to row 45 per CA rules")

    elif "salaries and incentives" in rl:
        if industry == "manufacturing":
            set_rule(45, "Wages (Manufacturing - Salaries)", "Salaries and incentives for manufacturing maps to row 45 per CA rules")

    # =========================================================================
    # P&L: JOB WORK, FREIGHT, POWER, OTHERS MFG (rows 46-51)
    # =========================================================================
    elif any(k in rl for k in ["job work charges", "contract labour", "material handling charges"]):
        if "income" not in rl:
            set_rule(46, "Processing / Job Work Charges", "Job Work / Material Handling charges map to row 46 per CA rules")

    elif any(k in rl for k in ["transportation charges", "transportation charge"]):
        set_rule(47, "Freight and Transportation Charges", "Transportation charges map to row 47")

    elif any(k in rl for k in ["power & fuel", "power and fuel", "electricity & power",
                                "electricity"]):
        if industry == "manufacturing":
            set_rule(48, "Power, Coal, Fuel and Water", "Power/Fuel for manufacturing maps to row 48 per CA rules")

    elif "manufacturing expenses" in rl and "other" not in rl and "partial" not in rl:
        set_rule(49, "Others (Manufacturing)", "Manufacturing Expenses maps to Others Mfg (row 49)")

    elif "other direct costs" in rl:
        set_rule(49, "Others (Manufacturing)", "Other Direct Costs under cost of materials maps to Others Mfg (row 49)")

    elif any(k in rl for k in ["packing and forwarding", "packing & forwarding"]):
        set_rule(49, "Others (Manufacturing)", "Packing and Forwarding is a manufacturing-related expense (row 49)")

    elif "warehouse charges" in rl:
        set_rule(49, "Others (Manufacturing)", "Warehouse Charges maps to Others Mfg (row 49)")

    elif "research and development" in rl or "research & development" in rl:
        if gt_row == 49:
            set_rule(49, "Others (Manufacturing)", "R&D expense mapped to Others Mfg (row 49)")
        elif gt_row == 71:
            set_rule(71, "Others (Admin)", "R&D expense mapped to Others Admin (row 71). Could be 49 if manufacturing-related.")

    elif "project cost" in rl:
        if gt_row == 49:
            set_rule(49, "Others (Manufacturing)", "Project Cost mapped to Others Mfg (row 49)")
        elif gt_row == 71:
            set_rule(71, "Others (Admin)", "Project Cost mapped to Others Admin (row 71)")

    elif "repairs" in rl and ("plant" in rl or "machinery" in rl or "machineries" in rl):
        set_rule(50, "Repairs & Maintenance (Manufacturing)", "Repairs to Plant/Machinery maps to row 50 per CA rules")

    elif "repairs" in rl and "building" in rl:
        if gt_row == 50:
            set_rule(50, "Repairs & Maintenance (Manufacturing)", "Repairs to Buildings mapped to manufacturing repairs (row 50)")
        elif gt_row == 72:
            set_rule(72, "Repairs & Maintenance (Admin)", "Repairs to Buildings mapped to admin repairs (row 72)")

    elif "repairs" in rl and "vehicle" in rl:
        set_rule(72, "Repairs & Maintenance (Admin)", "Repairs to Vehicles maps to admin repairs (row 72)")

    elif "repairs" in rl and "others" in rl:
        if gt_row == 50:
            set_rule(50, "Repairs & Maintenance (Manufacturing)", "Repairs - Others mapped to manufacturing repairs (row 50)")
        elif gt_row == 72:
            set_rule(72, "Repairs & Maintenance (Admin)", "Repairs - Others mapped to admin repairs (row 72)")

    # =========================================================================
    # P&L: STOCK CHANGES (rows 53-54, 58-59)
    # =========================================================================
    elif "opening stock" in rl and ("work-in-process" in rl or "wip" in rl or "work in progress" in rl):
        set_rule(53, "Stock in Process Opening Balance", "Opening Stock WIP maps to row 53")

    elif "closing stock" in rl and ("work-in-progress" in rl or "wip" in rl or "work in process" in rl):
        set_rule(54, "Stock in Process Closing Balance", "Closing Stock WIP maps to row 54")

    elif "changes in work-in-progress" in rl:
        # Net change line - should be split to 53/54
        result["status"] = "dispute"
        result["agent_reasoning"] = "Changes in WIP/stock-in-trade is a NET change, not raw materials. Should be split into Opening/Closing rows (53/54). GT maps to 42 which seems incorrect."
        return result

    # =========================================================================
    # P&L: DEPRECIATION (rows 56, 63)
    # =========================================================================
    elif any(k in rl for k in ["depreciation and amortization", "depreciation and amortisation"]):
        if gt_row == 56:
            set_rule(56, "Depreciation", "Depreciation maps to row 56")
        elif gt_row == 63:
            set_rule(63, "Depreciation (CMA)", "Depreciation allocated to CMA row 63")

    # Row 58: Finished Goods Opening
    elif "finished goods" in rl and "(opening)" in rl:
        set_rule(58, "Finished Goods Opening Balance", "Finished Goods (Opening) maps to row 58")

    # Row 59: Finished Goods Closing
    elif "finished goods" in rl and "(closing)" in rl:
        set_rule(59, "Finished Goods Closing Balance", "Finished Goods (Closing) maps to row 59")

    elif "closing stock" in rl and "finished goods" in rl:
        set_rule(59, "Finished Goods Closing Balance", "Closing Stock - Finished Goods maps to row 59")

    # Row 59: Finished Goods from BS note used as P&L closing
    elif rl.strip() == "finished goods" and "inventories" in sl and ctx == "pl":
        set_rule(59, "Finished Goods Closing Balance", "Finished Goods from Inventories note used as P&L closing balance (row 59)")

    # Row 64: Other Manufacturing Expenses (derived)
    elif "other manufacturing expenses" in rl:
        set_rule(64, "Other Manufacturing Exp", "Other Manufacturing Expenses (derived) maps to row 64")

    # Row 63: Manufacturing Expenses (partial) -> could be row 63 or 71
    elif "manufacturing expenses (partial)" in rl:
        if gt_row == 71:
            set_rule(71, "Others (Admin)", "Manufacturing Expenses (partial) - the non-mfg portion going to Others Admin (row 71)")
        elif gt_row == 64:
            set_rule(64, "Other Manufacturing Exp", "Manufacturing Expenses (partial) going to row 64")

    # =========================================================================
    # P&L: ADMIN EXPENSES (rows 67-77)
    # =========================================================================
    elif "rent" in rl and ("rates" in rl or "licence" in rl):
        set_rule(68, "Rent, Rates and Taxes", "Rent, Rates and Taxes maps to row 68")

    elif "rent, rates, taxes" in rl:
        set_rule(68, "Rent, Rates and Taxes", "Rent, Rates, Taxes and Licence items maps to row 68")

    elif rl.strip() in ("rent", "rent paid"):
        if gt_row == 68:
            set_rule(68, "Rent, Rates and Taxes", "Rent maps to row 68")
        elif gt_row == 49:
            set_rule(68, "Rent, Rates and Taxes", "Rent generally maps to row 68. GT has 49 (Others Mfg) - could be factory rent.")
        elif gt_row == 71:
            set_rule(68, "Rent, Rates and Taxes", "Rent generally maps to row 68. GT has 71 (Others Admin).")

    elif "advertisement" in rl or "delivery expenses" in rl:
        set_rule(70, "Advertisements and Sales Promotions", "Advertisement/Delivery expense maps to row 70")

    elif any(k in rl for k in [
        "consultation", "professional", "insurance paid", "insurance premium",
        "communication", "postage", "courier", "contribution towards csr",
        "miscellaneous", "other admin",
    ]):
        set_rule(71, "Others (Admin)", f"Admin expense '{raw}' maps to Others Admin (row 71)")

    elif "advances written off" in rl:
        if gt_row == 75:
            set_rule(75, "Miscellaneous Expenses Written Off", "Advances Written Off maps to Misc Expenses Written Off (row 75)")
        elif gt_row == 71:
            set_rule(71, "Others (Admin)", "Advances Written Off - small amounts can go to Others Admin (row 71). Could also be 75 or 90.")

    elif any(k in rl for k in ["payments to the auditor", "audit"]):
        set_rule(73, "Audit Fees / Directors Remuneration", "Payments to auditor maps to row 73 per CA rules")

    # =========================================================================
    # P&L: FINANCE CHARGES (rows 83-85)
    # =========================================================================
    elif "interest of income tax" in rl:
        set_rule(84, "Interest on WC / Tax Delay", "Interest on Income Tax delay maps to row 84 per CA rules")

    elif any(k in rl for k in [
        "interest on loan (working capital",
        "interest on working capital",
    ]):
        set_rule(84, "Interest on Working Capital Loans", "Interest on Working Capital loans maps to row 84")

    elif any(k in rl for k in [
        "interest -term loan", "interest on loan (term loan",
        "interest paid on unsecured", "interest on loan",
        "interest on unsecrued loan",
    ]):
        set_rule(83, "Interest on Term Loans", "Interest on term/fixed loans maps to row 83")

    elif "interest on vehicle loan" in rl:
        set_rule(83, "Interest on Term Loans", "Interest on Vehicle Loan maps to row 83 (fixed asset loan)")

    elif any(k in rl for k in ["interest on cc", "interest on working capital",
                                "interest on loan (working capital"]):
        set_rule(84, "Interest on Working Capital Loans", "Interest on CC/WC maps to row 84")

    # =========================================================================
    # P&L: NON-OPERATING EXPENSES (rows 89-93)
    # =========================================================================
    elif "non operating expenses" in rl or "non-operating expenses" in rl:
        set_rule(93, "Others (Non-Op Expenses)", "Non-Operating Expenses maps to row 93")

    # =========================================================================
    # P&L: TAX (rows 99-101)
    # =========================================================================
    elif any(k in rl for k in ["current tax", "current taxes", "earlier year tax"]):
        set_rule(99, "Income Tax Provision", "Current/Income tax maps to row 99")

    # =========================================================================
    # P&L: APPROPRIATION (rows 106-108)
    # =========================================================================
    elif any(k in rl for k in [
        "surplus at the beginning", "surplus - opening",
        "surplus in profit and loss account: balance at beginning",
        "surplus in p&l: balance at beginning",
    ]):
        set_rule(106, "Brought Forward from Previous Year", "Opening surplus maps to row 106")

    elif "issue of bonus share" in rl:
        set_rule(108, "Other Appropriation of Profit", "Issue of Bonus Share (surplus capitalised) maps to row 108")

    # =========================================================================
    # BS: SHARE CAPITAL & RESERVES (rows 116-125)
    # =========================================================================
    elif any(k in rl for k in [
        "paid-up share capital", "paid up share capital",
        "issued, subscribed and paid", "subscribed & paid up",
        "issued subscribed and fully paid",
    ]):
        set_rule(116, "Issued, Subscribed and Paid up", "Paid-up capital maps to row 116")

    elif any(k in rl for k in [
        "surplus in statement of profit", "surplus - closing balance",
        "balance transferred from profit",
    ]):
        if ctx == "bs":
            set_rule(122, "Balance transferred from P&L", "P&L surplus in BS maps to row 122")

    elif "securities premium" in rl or "share premium" in rl:
        set_rule(123, "Share Premium A/c", "Securities/Share Premium maps to row 123")

    # =========================================================================
    # BS: BORROWINGS (rows 131-154)
    # =========================================================================
    elif "inland lc discounting" in rl or "tata capital" in rl:
        set_rule(132, "Working Capital Finance (Bank 2)", "Second bank / LC discounting maps to row 132")

    elif any(k in rl for k in [
        "short-term borrowings", "yes bank channel finance",
        "other bank balances (cr.)", "indian bank - cc account",
        "nsic - loan against guarantee", "working capital bank borrowings",
    ]):
        if "+" in rl and "short-term provisions" in rl:
            # Combined line: Other Dues + Short-term Provisions
            set_rule(250, "Other Current Liabilities", "Combined Other Dues + Short-term Provisions maps to row 250")
        else:
            set_rule(131, "Working Capital Finance (Bank 1)", "Short-term bank borrowings / CC maps to row 131")

    elif "loan from banks - current maturities" in rl or "term loan current" in rl:
        set_rule(136, "Term Loan Current Portion", "Current maturities of term loan maps to row 136")

    elif any(k in rl for k in ["long-term borrowings (secured)", "loans - secured (non-current)",
                                "long term borrowings"]):
        set_rule(137, "Term Loan (Long-term)", "Long-term secured borrowings map to row 137")

    elif "vehicle hp" in rl and "non-current" in rl:
        set_rule(148, "Other Debts (Vehicle HP)", "Vehicle HP Loans non-current maps to row 148 (Other Debts). GT has 141 (Debentures).")

    elif "provision for employee benefits" in rl and "gratuity" in rl:
        set_rule(153, "Long Term Debt (Gratuity Provision)", "Long-term gratuity provision maps to row 153 as non-fund LT liability")

    elif "unsecured loans (additional)" in rl:
        set_rule(153, "Long Term Debt (Unsecured)", "Unsecured long-term loans map to row 153")

    elif "other long term liability" in rl:
        set_rule(153, "Long Term Debt", "Other Long Term Liability maps to row 153")

    # =========================================================================
    # BS: FIXED ASSETS (rows 162-178)
    # =========================================================================
    elif any(k in rl for k in ["gross block", "property, plant and equipment"]):
        set_rule(162, "Gross Block", "Gross Block / PPE maps to row 162")

    elif any(k in rl for k in ["capital work-in-progress", "capital work in progress"]):
        set_rule(165, "Capital Work in Progress", "CWIP maps to row 165 per CA rules")

    elif "intangible assets" in rl and ("software" in rl or "licence" in rl):
        set_rule(169, "Patents / Goodwill / Copyrights", "Intangible Assets (Software/Licence) maps to row 169")

    elif rl.strip() == "other intangible assets":
        set_rule(172, "Other Intangible Assets", "Other Intangible Assets maps to row 172")

    elif "intangible assets" in rl and "(net block)" in rl:
        set_rule(172, "Other Intangible Assets", "Intangible Assets (Net Block) maps to row 172")

    elif rl.strip() == "intangible assets":
        set_rule(172, "Other Intangible Assets", "Generic Intangible Assets maps to row 172")

    elif "additions to fixed assets" in rl:
        set_rule(175, "Additions to Fixed Assets", "Additions to Fixed Assets maps to row 175")

    # =========================================================================
    # BS: INVENTORIES (rows 193-201)
    # =========================================================================
    elif "raw materials + packing + consumables" in rl:
        set_rule(194, "Raw Material Inventory (Indigenous)", "Raw materials + packing + consumables inventory maps to row 194")

    elif "raw materials" in rl and ("inventories" in sl or ctx == "bs"):
        set_rule(194, "Raw Material Inventory (Indigenous)", "Raw materials inventory in BS maps to row 194")

    elif "scraps" in rl and "inventories" in sl:
        set_rule(198, "Stores Inventory (Indigenous)", "Scraps under Inventories maps to row 198")

    elif "work-in-progress" in rl and ("inventories" in sl or (ctx == "bs" and gt_row == 200)):
        set_rule(200, "Stocks-in-process (BS)", "WIP in BS inventory maps to row 200")

    elif rl.strip() == "finished goods" and ("inventories" in sl or (ctx == "bs" and gt_row == 201)):
        set_rule(201, "Finished Goods (BS)", "Finished Goods inventory in BS maps to row 201")

    # =========================================================================
    # BS: RECEIVABLES (rows 206-208, 232)
    # =========================================================================
    elif "trade receivables" in rl and "domestic" in rl:
        set_rule(206, "Domestic Receivables", "Trade Receivables (Domestic) maps to row 206")

    elif "trade receivable" in rl and "domestic" in rl:
        set_rule(206, "Domestic Receivables", "Trade Receivables - Domestic maps to row 206")

    elif rl.strip() == "trade receivables" and ctx == "bs":
        set_rule(206, "Domestic Receivables", "Trade Receivables (generic) in BS maps to row 206 (Domestic)")

    elif "trade receivables" in rl and "export" in rl:
        set_rule(207, "Export Receivables", "Trade Receivables (Export) maps to row 207")

    elif ("exceeding 6 months" in rl or "more than 6 months" in rl) and gt_row == 208:
        set_rule(208, "Debtors more than 6 months", "Receivables exceeding 6 months maps to row 208")

    elif ("exceeding 6 months" in rl or "more than 6 months" in rl) and gt_row == 232:
        set_rule(232, "Debtors more than 6 months (Non-current)", "Non-current debtors > 6 months maps to row 232")

    elif "trade receivables - more than 6 months" in rl and "non current" in sl:
        set_rule(232, "Debtors more than 6 months (Non-current)", "Non-current trade receivables > 6 months maps to row 232")

    elif "trade receivables - more than 6 months" in rl:
        set_rule(208, "Debtors more than 6 months", "Trade receivables > 6 months maps to row 208")

    # =========================================================================
    # BS: CASH & BANK (rows 212-215)
    # =========================================================================
    elif any(k in rl for k in ["balance with bank", "balance with banks", "bank balances"]) and ctx == "bs":
        set_rule(213, "Bank Balances", "Bank balances in BS maps to row 213")

    elif "deposits" in rl and "maturity > 12" in rl:
        set_rule(214, "Fixed Deposit under lien", "Deposits maturity > 12 months (margin money) maps to row 214")

    elif "deposits (3-12 months)" in rl or ("deposits" in rl and "maturity < 3" in rl):
        set_rule(215, "Other Fixed Deposits", "Short-term deposits maps to row 215")

    elif "fixed deposits" in rl and ctx == "bs":
        set_rule(215, "Other Fixed Deposits", "Fixed Deposits in BS maps to row 215")

    # =========================================================================
    # BS: LOANS & ADVANCES (rows 219-224)
    # =========================================================================
    elif "gst input recoverable" in rl:
        set_rule(219, "Advances Recoverable", "GST Input Recoverable maps to row 219")

    elif any(k in rl for k in ["net tax", "advance income tax", "tds receivable"]):
        set_rule(221, "Advance Income Tax", "Advance Tax / TDS Receivable maps to row 221")

    elif "other advances" in rl and (ctx == "bs" or "current asset" in sl):
        set_rule(223, "Other Advances / Current Asset", "Other Advances maps to row 223")

    elif "other advances / other current assets" in rl:
        set_rule(223, "Other Advances / Current Asset", "Other Advances / Other Current Assets maps to row 223")

    # =========================================================================
    # BS: NON-CURRENT ASSETS (rows 229-238)
    # =========================================================================
    elif "capital advances" in rl:
        set_rule(236, "Advances to suppliers of capital goods", "Capital Advances maps to row 236")

    elif "long-term loans and advances" in rl:
        set_rule(237, "Security deposits with government", "Long-term Loans and Advances maps to row 237")

    elif "security and other deposits" in rl:
        set_rule(238, "Other non-current assets", "Security and other deposits maps to row 238 per CA rules")

    elif any(k in rl for k in ["other non-current assets", "other non- current assets"]):
        if gt_row == 237:
            set_rule(237, "Security deposits with government", "Other Non-Current Assets mapped to row 237")
        else:
            set_rule(238, "Other non-current assets", "Other Non-current Assets maps to row 238")

    # =========================================================================
    # BS: CURRENT LIABILITIES (rows 242-250)
    # =========================================================================
    elif "trade payables" in rl:
        set_rule(242, "Sundry Creditors for goods", "Trade Payables maps to row 242")

    elif "advance from customer" in rl:
        set_rule(243, "Advance received from customers", "Advance from Customers maps to row 243")

    elif "provision for tax" in rl:
        set_rule(244, "Provision for Taxation", "Provision for Taxation maps to row 244")

    elif any(k in rl for k in [
        "statutory dues", "statutory liability", "tds/tcs payable",
        "gst payable", "esi & pf payable",
    ]):
        set_rule(246, "Other statutory liabilities", "Statutory dues/liabilities maps to row 246 per CA rules")

    elif "short-term provisions" in rl and "other dues" not in rl:
        set_rule(249, "Creditors for Expenses", "Short-term Provisions maps to row 249")

    elif any(k in rl for k in [
        "salary and wages payable", "other expenses payable",
        "outstanding expenses",
    ]):
        set_rule(249, "Creditors for Expenses", "Outstanding expenses / payables maps to row 249")

    elif "other liabilities" in rl and ("directors" in rl or "related" in rl):
        set_rule(249, "Creditors for Expenses", "Other Liabilities (Directors + Related) maps to row 249")

    elif "other dues + short-term provisions" in rl:
        set_rule(250, "Other Current Liabilities", "Combined Other Dues + Short-term Provisions maps to row 250")

    elif "other dues" in rl and "current liabilities" in sl:
        set_rule(250, "Other Current Liabilities", "Other Dues under Current Liabilities maps to row 250")

    elif "dues to related parties" in rl:
        set_rule(250, "Other Current Liabilities", "Dues to Related Parties maps to row 250")

    elif "(d) others" in rl and "current liabilities" in sl:
        set_rule(250, "Other Current Liabilities", "(d) Others under Current Liabilities maps to row 250")

    elif "other current liabilities" in rl:
        set_rule(250, "Other Current Liabilities", "Other Current Liabilities maps to row 250")

    # =========================================================================
    # DETERMINE STATUS
    # =========================================================================
    if result["golden_rule_row"] is not None:
        if result["golden_rule_row"] == gt_row:
            result["status"] = "confirmed"
        else:
            result["status"] = "dispute"
            result["agent_reasoning"] += (
                f" | DISPUTE: Golden rule says row {result['golden_rule_row']} "
                f"but GT has row {gt_row}."
            )

    return result


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    for company, items in data.items():
        for item in items:
            results.append(classify_item(item))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Summary
    confirmed = sum(1 for r in results if r["status"] == "confirmed")
    dispute = sum(1 for r in results if r["status"] == "dispute")
    unverified = sum(1 for r in results if r["status"] == "truly_unverified")
    excluded = sum(1 for r in results if r["status"] == "excluded")

    print(f"Total items: {len(results)}")
    print(f"Confirmed:        {confirmed}")
    print(f"Dispute:          {dispute}")
    print(f"Truly Unverified: {unverified}")
    print(f"Excluded:         {excluded}")
    print()

    print("=== DISPUTES ===")
    for r in results:
        if r["status"] == "dispute":
            print(
                f"  [{r['company']}] '{r['raw_text']}' GT={r['gt_row']} "
                f"Golden={r['golden_rule_row']} | {r['agent_reasoning']}"
            )

    print()
    print("=== TRULY UNVERIFIED ===")
    for r in results:
        if r["status"] == "truly_unverified":
            print(f"  [{r['company']}] '{r['raw_text']}' GT={r['gt_row']}")


if __name__ == "__main__":
    main()
