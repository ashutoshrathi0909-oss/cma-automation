"use client";

import { useRef, useState } from "react";
import { ChevronDown, X } from "lucide-react";
import { Input } from "@/components/ui/input";

// All CMA field names from the INPUT SHEET mapping (cma_field_rows.py)
const CMA_FIELDS: string[] = [
  // P&L fields
  "Domestic Sales",
  "Export Sales",
  "Less Excise Duty and Cess",
  "Dividends received from Mutual Funds",
  "Interest Received",
  "Profit on sale of fixed assets / Investments",
  "Gain on Exchange Fluctuations",
  "Extraordinary income",
  "Others (Non-Operating Income)",
  "Raw Materials Consumed (Imported)",
  "Raw Materials Consumed (Indigenous)",
  "Stores and spares consumed (Imported)",
  "Stores and spares consumed (Indigenous)",
  "Wages",
  "Processing / Job Work Charges",
  "Freight and Transportation Charges",
  "Power, Coal, Fuel and Water",
  "Others (Manufacturing)",
  "Repairs & Maintenance (Manufacturing)",
  "Security Service Charges",
  "Stock in process Opening Balance",
  "Stock in process Closing Balance",
  "Depreciation (Manufacturing)",
  "Finished Goods Opening Balance",
  "Finished Goods Closing Balance",
  "Depreciation (CMA)",
  "Other Manufacturing Exp (CMA)",
  "Salary and staff expenses",
  "Rent, Rates and Taxes",
  "Bad Debts",
  "Advertisements and Sales Promotions",
  "Others (Admin)",
  "Repairs & Maintenance (Admin)",
  "Audit Fees & Directors Remuneration",
  "Miscellaneous Expenses written off",
  "Deferred Revenue Expenditures",
  "Other Amortisations",
  "Interest on Fixed Loans / Term loans",
  "Interest on Working capital loans",
  "Bank Charges",
  "Loss on sale of fixed assets / Investments",
  "Sundry Balances Written off",
  "Loss on Exchange Fluctuations",
  "Extraordinary losses",
  "Others (Non-Operating Expenses)",
  "Income Tax provision",
  "Deferred Tax Liability (P&L)",
  "Deferred Tax Asset (P&L)",
  "Brought forward from previous year",
  "Dividend",
  "Other Appropriation of profit",
  // Balance Sheet fields
  "Issued, Subscribed and Paid up",
  "Share Application Money",
  "General Reserve",
  "Balance transferred from profit and loss a/c",
  "Share Premium A/c",
  "Revaluation Reserve",
  "Other Reserve",
  "Working Capital Bank Finance - Bank 1",
  "Working Capital Bank Finance - Bank 2",
  "Term Loan Repayable in next one year",
  "Term Loan Balance Repayable after one year",
  "Debentures Repayable in next one year",
  "Debentures Balance Repayable after one year",
  "Preference Shares Repayable in next one year",
  "Preference Shares Balance Repayable after one year",
  "Other Debts Repayable in Next One year",
  "Balance Other Debts",
  "Unsecured Loans - Quasi Equity",
  "Unsecured Loans - Long Term Debt",
  "Unsecured Loans - Short Term Debt",
  "Deferred tax liability (BS)",
  "Gross Block",
  "Less Accumulated Depreciation",
  "Capital Work in Progress",
  "Patents / goodwill / copyrights etc",
  "Misc Expenditure (to the extent not w/o)",
  "Deferred Tax Asset (BS)",
  "Other Intangible assets",
  "Additions to Fixed Assets",
  "Sale of Fixed assets WDV",
  "Profit on sale of Fixed assets (BS)",
  "Loss on sale of Fixed assets (BS)",
  "Investment in Govt. Securities (Current)",
  "Investment in Govt. Securities (Non Current)",
  "Other current investments",
  "Other non current investments",
  "Investment in group companies / subsidiaries",
  "Raw Material Imported",
  "Raw Material Indigenous",
  "Stores and Spares Imported",
  "Stores and Spares Indigenous",
  "Stocks-in-process",
  "Finished Goods",
  "Domestic Receivables",
  "Export Receivables",
  "Debtors more than 6 months",
  "Cash on Hand",
  "Bank Balances",
  "Fixed Deposit under lien",
  "Other Fixed Deposits",
  "Advances recoverable in cash or in kind",
  "Advances to suppliers of raw materials",
  "Advance Income Tax",
  "Prepaid Expenses",
  "Other Advances / current asset",
  "Advances to group / subsidiaries companies",
  "Exposure in group companies - Investments",
  "Exposure in group companies - Advances",
  "Debtors more than six months (Non-Current)",
  "Investments (Non-Current)",
  "Fixed Deposits (Non Current)",
  "Dues from directors / partners / promoters",
  "Advances to suppliers of capital goods",
  "Security deposits with government departments",
  "Other non current assets",
  "Sundry Creditors for goods",
  "Advance received from customers",
  "Provision for Taxation",
  "Dividend payable",
  "Other statutory liabilities (due within 1 year)",
  "Interest Accrued but not due",
  "Interest Accrued and due",
  "Creditors for Expenses",
  "Other current liabilities",
  "Arrears of cumulative dividends",
  "Gratuity liability not provided for",
  "Disputed excise / customs / tax liabilities",
  "Bank guarantee / Letter of credit outstanding",
  "Other contingent liabilities",
];

interface CMAFieldSelectorProps {
  value: string | null;
  onChange: (field: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function CMAFieldSelector({
  value,
  onChange,
  disabled = false,
  placeholder = "Search CMA field…",
}: CMAFieldSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const filtered = search.trim()
    ? CMA_FIELDS.filter((f) =>
        f.toLowerCase().includes(search.toLowerCase())
      )
    : CMA_FIELDS;

  function handleSelect(field: string) {
    onChange(field);
    setSearch("");
    setOpen(false);
  }

  function handleClear(e: React.MouseEvent) {
    e.stopPropagation();
    onChange("");
    setSearch("");
  }

  function handleBlur() {
    // Delay so click on option registers first
    closeTimer.current = setTimeout(() => setOpen(false), 150);
  }

  function handleFocus() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpen(true);
  }

  return (
    <div className="relative">
      <div className="relative flex items-center">
        <Input
          value={open ? search : (value ?? "")}
          onChange={(e) => setSearch(e.target.value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={value ?? placeholder}
          disabled={disabled}
          className="pr-8"
        />
        {value && !disabled ? (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : (
          <ChevronDown className="pointer-events-none absolute right-2 h-3.5 w-3.5 text-muted-foreground" />
        )}
      </div>

      {open && !disabled && (
        <div className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-md border bg-popover text-popover-foreground shadow-md">
          {filtered.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              No fields match "{search}"
            </p>
          ) : (
            filtered.map((field) => (
              <button
                key={field}
                type="button"
                onMouseDown={() => handleSelect(field)}
                className={`w-full px-3 py-1.5 text-left text-sm hover:bg-accent hover:text-accent-foreground ${
                  value === field ? "bg-accent font-medium" : ""
                }`}
              >
                {field}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
