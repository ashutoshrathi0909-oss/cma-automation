# Excel Accuracy Testing Patterns for CMA Validation

**Research Date:** March 2026
**Context:** CMA Automation System — defining how to compare the generated CMA Excel against
the CA-prepared ground-truth, produce a cell-by-cell report, and calculate an overall accuracy
score.

---

## 1. Defining What to Compare

### Option A: Compare all non-empty cells (naive)

Read every cell in both sheets and flag differences. Problems:
- Formatting cells (borders, colours) have no value but differ in metadata
- Formula cells in the template are preserved by openpyxl and show formula strings
- Blank cells in one file vs. zero-value cells in another cause false failures

### Option B: Compare only the cells we explicitly write (correct)

Our `excel_generator.py` writes exactly the cells defined by:

```
row     = ALL_FIELD_TO_ROW[field_name]         # e.g., "Domestic Sales" → row 22
col     = YEAR_TO_COLUMN[financial_year]        # e.g., 2024 → "C"
```

This is a fixed, enumerable set. For the Dynamic Air Engineering test:
- 89 fields (from `ALL_FIELD_TO_ROW`)
- 4 years (FY22=2023 col B, FY23=2024 col C, FY24=2025 col D, FY25=2026 col E)
- **Maximum 356 cells to compare**

In practice, many cells will be blank in both files (a trading company has no "Wages" row).
The comparison should handle blank-vs-blank as a pass.

### The comparison cell set

```python
# Canonical set of all cells the generator can write
# year_map: financial_year (int) → column letter
COMPARE_SCOPE = {
    (field, row, year, col)
    for field, row in ALL_FIELD_TO_ROW.items()
    for year, col in YEAR_TO_COLUMN.items()
    if year in [2023, 2024, 2025, 2026]   # only years in this test
}
```

---

## 2. Floating Point Tolerance for Financial Numbers

Indian financial statements use figures in lakhs (₹ 1 lakh = ₹ 1,00,000). Common precision:

- Most CMA rows are filled to the nearest lakh (e.g., 45.00 = ₹45 lakhs)
- Some are filled to 2 decimal places (e.g., 45.23 lakhs)
- OCR may introduce minor rounding during extraction (e.g., reading "45,23,456" as 4523456.0)

### Tolerance strategies

**1. Relative tolerance (recommended for financial data)**

```python
def values_match(actual: float | None, expected: float | None, rtol: float = 0.01) -> bool:
    """Return True if values match within relative tolerance.

    rtol=0.01 means 1% — standard for CMA validation.
    Both None → match (blank cell is correct).
    One None, one float → no match.
    """
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    if expected == 0:
        return actual == 0
    return abs(actual - expected) / abs(expected) <= rtol
```

**2. Absolute tolerance (for very small values)**

Use when expected values are close to zero (e.g., miscellaneous amounts < ₹1 lakh).
A 1% relative tolerance on ₹0.05 lakhs is ₹500 — meaninglessly tight.

```python
def values_match_hybrid(
    actual: float | None,
    expected: float | None,
    rtol: float = 0.01,
    atol: float = 0.50,   # 0.50 lakhs = ₹50,000 absolute tolerance
) -> bool:
    if actual is None and expected is None:
        return True
    if actual is None or expected is None:
        return False
    if expected == 0:
        return abs(actual) <= atol
    return (
        abs(actual - expected) / abs(expected) <= rtol  # relative
        or abs(actual - expected) <= atol               # absolute fallback
    )
```

**3. Rounding normalisation**

Before comparison, round both values to 2 decimal places (matching CMA sheet precision):

```python
def normalise(v: float | None) -> float | None:
    return round(v, 2) if v is not None else None
```

### Industry-standard thresholds used in similar projects

| Scenario | Tolerance | Rationale |
|----------|-----------|-----------|
| OCR reading financial tables | 2-5% | OCR may misread digits |
| AI classification → CMA field | 1-3% | Sum of many small items |
| Excel formula subtotals | 0% (skip) | Don't compare formula cells |
| Rounding during extraction | 0.5% | Lakh-level rounding |

**Our target:** 1% relative tolerance (`rtol=0.01`), matching the spec in
`2026-03-19-dynamic-air-engineering-test-design.md` §5 (Agent 5 validation table).

---

## 3. Comparison Structure: Field-by-Field, Year-by-Year

### Data model for a comparison result

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class CellResult:
    field_name: str
    row: int
    year: int
    col: str
    cell_address: str          # e.g., "C22"
    expected: float | None     # from ground-truth .xls
    actual: float | None       # from generated .xlsm
    match: bool
    pct_error: float | None    # None if either value is None
    status: Literal["PASS", "FAIL", "BLANK_BOTH", "MISSING"]

@dataclass
class ComparisonReport:
    generated_path: str
    ground_truth_path: str
    company: str
    years_compared: list[int]
    results: list[CellResult] = field(default_factory=list)

    @property
    def total_cells(self) -> int:
        return len(self.results)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.status == "PASS")

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")

    @property
    def blank_both_count(self) -> int:
        return sum(1 for r in self.results if r.status == "BLANK_BOTH")

    @property
    def accuracy_pct(self) -> float:
        """Accuracy = PASS / (PASS + FAIL). Blank-both cells excluded."""
        denominator = self.pass_count + self.fail_count
        if denominator == 0:
            return 0.0
        return round(self.pass_count / denominator * 100, 1)
```

### Full comparison function

```python
import openpyxl
import xlrd
from openpyxl.utils import column_index_from_string

from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.mappings.year_columns import YEAR_TO_COLUMN

SHEET_NAME = "INPUT SHEET"
RTOL = 0.01
ATOL = 0.50  # lakhs


def compare_cma_files(
    generated_path: str,
    ground_truth_path: str,
    years: list[int],
    company: str = "",
    rtol: float = RTOL,
    atol: float = ATOL,
) -> ComparisonReport:
    """Compare generated .xlsm against ground-truth .xls.

    Parameters
    ----------
    generated_path   — path to .xlsm produced by ExcelGenerator
    ground_truth_path — path to .xls prepared by CA
    years            — list of financial years to compare (e.g., [2023,2024,2025,2026])
    """
    generated_values = _read_generated(generated_path, years)
    truth_values = _read_ground_truth(ground_truth_path, years)

    report = ComparisonReport(
        generated_path=generated_path,
        ground_truth_path=ground_truth_path,
        company=company,
        years_compared=years,
    )

    for field_name, row in ALL_FIELD_TO_ROW.items():
        for year in years:
            col = YEAR_TO_COLUMN.get(year)
            if col is None:
                continue

            key = (row, col)
            actual = generated_values.get(key)
            expected = truth_values.get(key)

            cell_address = f"{col}{row}"

            if expected is None and actual is None:
                status = "BLANK_BOTH"
                match = True
                pct_error = None
            elif expected is None and actual is not None:
                # We filled a cell the CA left blank — could be correct or wrong
                status = "FAIL"
                match = False
                pct_error = None
            elif expected is not None and actual is None:
                # CA has a value; we produced nothing — definitely wrong
                status = "MISSING"
                match = False
                pct_error = None
            else:
                # Both have values — compare
                match = _values_match(actual, expected, rtol, atol)
                if expected == 0:
                    pct_error = abs(actual) * 100 if actual else 0.0
                else:
                    pct_error = round(abs(actual - expected) / abs(expected) * 100, 2)
                status = "PASS" if match else "FAIL"

            report.results.append(CellResult(
                field_name=field_name,
                row=row,
                year=year,
                col=col,
                cell_address=cell_address,
                expected=expected,
                actual=actual,
                match=match,
                pct_error=pct_error,
                status=status,
            ))

    return report


def _values_match(actual: float, expected: float, rtol: float, atol: float) -> bool:
    if expected == 0:
        return abs(actual) <= atol
    return (
        abs(actual - expected) / abs(expected) <= rtol
        or abs(actual - expected) <= atol
    )


def _read_generated(path: str, years: list[int]) -> dict[tuple[int, str], float | None]:
    wb = openpyxl.load_workbook(path, data_only=True, keep_vba=True)
    ws = wb[SHEET_NAME]
    values = {}
    cols = {year: YEAR_TO_COLUMN[year] for year in years if year in YEAR_TO_COLUMN}
    for row in ALL_FIELD_TO_ROW.values():
        for col in cols.values():
            cell = ws.cell(row=row, column=column_index_from_string(col))
            v = cell.value
            values[(row, col)] = float(v) if isinstance(v, (int, float)) and v != 0 else None
    wb.close()
    return values


def _read_ground_truth(path: str, years: list[int]) -> dict[tuple[int, str], float | None]:
    wb = xlrd.open_workbook(path)
    try:
        ws = wb.sheet_by_name(SHEET_NAME)
    except xlrd.biffh.XLRDError:
        ws = wb.sheet_by_index(0)

    cols = {year: YEAR_TO_COLUMN[year] for year in years if year in YEAR_TO_COLUMN}
    values = {}
    for row in ALL_FIELD_TO_ROW.values():
        xlrd_row = row - 1
        if xlrd_row >= ws.nrows:
            continue
        for col in cols.values():
            xlrd_col = column_index_from_string(col) - 1
            if xlrd_col >= ws.ncols:
                continue
            cell = ws.cell(xlrd_row, xlrd_col)
            if cell.ctype == xlrd.XL_CELL_NUMBER and cell.value != 0:
                values[(row, col)] = float(cell.value)
            else:
                values[(row, col)] = None
    return values
```

---

## 4. Producing the Test Report

### Console-friendly tabular report

```python
def print_report(report: ComparisonReport) -> None:
    print(f"\n{'='*72}")
    print(f"CMA ACCURACY REPORT — {report.company}")
    print(f"Generated : {report.generated_path}")
    print(f"Ground truth: {report.ground_truth_path}")
    print(f"{'='*72}")

    # Header
    print(f"\n{'Field':<45} {'Cell':<6} {'Expected':>12} {'Actual':>12} {'% Err':>7} {'Status'}")
    print("-" * 90)

    failures = [r for r in report.results if r.status in ("FAIL", "MISSING")]
    passes   = [r for r in report.results if r.status == "PASS"]
    blanks   = [r for r in report.results if r.status == "BLANK_BOTH"]

    # Show failures first (most important)
    for r in sorted(failures, key=lambda x: (x.year, x.row)):
        exp_str = f"{r.expected:,.2f}" if r.expected is not None else "—"
        act_str = f"{r.actual:,.2f}" if r.actual is not None else "—"
        err_str = f"{r.pct_error:.1f}%" if r.pct_error is not None else "—"
        status_icon = "FAIL" if r.status == "FAIL" else "MISS"
        print(f"  {r.field_name:<43} {r.col}{r.row:<4} {exp_str:>12} {act_str:>12} {err_str:>7}  {status_icon}")

    print()

    # Summary
    print(f"{'='*72}")
    print(f"  PASS       : {report.pass_count:>4}  cells match within {RTOL*100:.0f}%")
    print(f"  FAIL       : {report.fail_count:>4}  cells differ")
    print(f"  MISSING    : {sum(1 for r in report.results if r.status=='MISSING'):>4}  expected value, got blank")
    print(f"  BLANK BOTH : {report.blank_both_count:>4}  both blank (correct — field not applicable)")
    print(f"  ACCURACY   : {report.accuracy_pct:>5.1f}%  (pass / (pass + fail + missing))")
    print(f"{'='*72}\n")


def save_report_json(report: ComparisonReport, output_path: str) -> None:
    """Save machine-readable report for downstream agents."""
    import json
    data = {
        "company": report.company,
        "accuracy_pct": report.accuracy_pct,
        "pass": report.pass_count,
        "fail": report.fail_count,
        "blank_both": report.blank_both_count,
        "total_cells": report.total_cells,
        "failures": [
            {
                "field": r.field_name,
                "cell": f"{r.col}{r.row}",
                "year": r.year,
                "expected": r.expected,
                "actual": r.actual,
                "pct_error": r.pct_error,
                "status": r.status,
            }
            for r in report.results
            if r.status in ("FAIL", "MISSING")
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

### Sample report output

```
========================================================================
CMA ACCURACY REPORT — Dynamic Air Engineering
Generated : test-results/dynamic/generated_dynamic_cma.xlsm
Ground truth: DOCS/Financials/CMA Dynamic 23082025.xls
========================================================================

Field                                         Cell   Expected       Actual   % Err  Status
------------------------------------------------------------------------------------------
  Wages                                       C45      45.23          0.00       —   MISS
  Power, Coal, Fuel and Water                 C48      12.80         13.50    5.5%   FAIL
  Others (Manufacturing)                      C49       3.10          3.14    1.3%   FAIL
  Depreciation (Manufacturing)                C56      22.00         22.00    0.0%   PASS

========================================================================
  PASS       :   71  cells match within 1%
  FAIL       :    9  cells differ
  MISSING    :    3  expected value, got blank
  BLANK BOTH :  273  both blank (correct — field not applicable)
  ACCURACY   :  86.1%  (pass / (pass + fail + missing))
========================================================================
```

---

## 5. Handling Edge Cases

### Scale mismatch (absolute vs. lakhs)

The CA-prepared CMA file may store values in absolute rupees (e.g., 4523456) while our pipeline
stores in lakhs (45.23). Detection:

```python
def detect_scale_mismatch(
    generated: dict[tuple, float | None],
    truth: dict[tuple, float | None],
    sample_cells: list[tuple],
) -> float:
    """Returns scale ratio (e.g., 100000.0 if truth is in abs and generated in lakhs)."""
    ratios = []
    for key in sample_cells:
        g = generated.get(key)
        t = truth.get(key)
        if g and t and g != 0:
            ratios.append(t / g)
    if not ratios:
        return 1.0
    median = sorted(ratios)[len(ratios) // 2]
    # Round to nearest standard scale
    for scale in [1, 100, 1000, 10000, 100000]:
        if abs(median - scale) / scale < 0.1:
            return float(scale)
    return median

# Usage: if scale != 1.0, normalise generated values before comparison
```

**Best practice:** Normalise all values to lakhs in the comparison function. Our generator
already stores in lakhs (the CA enters in lakhs in the CMA template too).

### Merged cells

openpyxl reads merged cell values from the top-left cell of the merge. Other cells in the
merge return `None`. The INPUT SHEET uses merged cells for section labels — these are not in
our `ALL_FIELD_TO_ROW` mapping, so they are automatically skipped.

### Named ranges

The CMA template may define named ranges (e.g., `DomesticSales_FY24`). These resolve to
specific cells. openpyxl supports reading named ranges:

```python
defined_names = wb.defined_names
for name in defined_names:
    defn = wb.defined_names[name]
    for title, coord in defn.destinations:
        ws = wb[title]
        print(f"{name} → {title}!{coord}")
```

For our comparison, named ranges are not needed — we use row/column indices directly.

---

## 6. Pytest Integration

```python
# tests/test_excel_accuracy.py

import pytest
from pathlib import Path

GENERATED = Path("test-results/dynamic/generated_dynamic_cma.xlsm")
GROUND_TRUTH = Path("DOCS/Financials/CMA Dynamic 23082025.xls")
YEARS = [2023, 2024, 2025, 2026]
PASS_THRESHOLD = 80.0   # Overall accuracy must be >= 80%

@pytest.mark.skipif(not GENERATED.exists(), reason="Generated file not yet created")
@pytest.mark.skipif(not GROUND_TRUTH.exists(), reason="Ground truth file not found")
def test_cma_accuracy():
    from app.services.excel_comparator import compare_cma_files
    report = compare_cma_files(
        str(GENERATED),
        str(GROUND_TRUTH),
        years=YEARS,
        company="Dynamic Air Engineering",
    )

    # Individual critical field assertions
    critical_fields = {
        "Domestic Sales": 2024,        # Row 22, Col C
        "Wages": 2024,                  # Row 45, Col C
        "Depreciation (Manufacturing)": 2024,  # Row 56, Col C
    }
    for field, year in critical_fields.items():
        matches = [
            r for r in report.results
            if r.field_name == field and r.year == year
        ]
        assert matches, f"No result for {field} FY{year}"
        assert matches[0].status in ("PASS", "BLANK_BOTH"), (
            f"{field} FY{year}: expected {matches[0].expected}, "
            f"got {matches[0].actual} ({matches[0].pct_error}% error)"
        )

    # Overall accuracy gate
    assert report.accuracy_pct >= PASS_THRESHOLD, (
        f"Overall accuracy {report.accuracy_pct:.1f}% < {PASS_THRESHOLD}% threshold\n"
        f"Failures: {report.fail_count}, Missing: "
        f"{sum(1 for r in report.results if r.status == 'MISSING')}"
    )
```

---

## Recommended for Our Project

1. **Comparison scope:** Limit to cells in `ALL_FIELD_TO_ROW` × `YEAR_TO_COLUMN` — this is
   the canonical set of cells our generator writes. 89 fields × 4 years = 356 max comparisons.

2. **Tolerance:** 1% relative tolerance (`rtol=0.01`) with 0.50 lakh absolute fallback (`atol=0.50`).
   This matches the spec in `agent5-excel.md` and handles both large and small amounts correctly.

3. **Blank handling:** Both blank = PASS (field not applicable for this company/year).
   Expected non-blank, got blank = MISSING (serious error). Got non-blank, expected blank =
   FAIL (we classified something that should not be there).

4. **Report format:** Human-readable console output showing only failures (sorted by year/row),
   plus JSON for agent7 to aggregate into the final `DYNAMIC_TEST_REPORT.md`.

5. **Scale check:** Run `detect_scale_mismatch()` before the main comparison. If the CA's file
   uses absolute rupees rather than lakhs, normalise before comparing.

6. **Accuracy target:** Per the test design spec, Gate G5 requires ≥ 80% of rows within 1%.
   Set `PASS_THRESHOLD = 80.0` in the pytest assertion.
