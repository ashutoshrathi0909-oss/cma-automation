# Python Excel Comparison Libraries for .xlsm Files

**Research Date:** March 2026
**Context:** CMA Automation System — comparing a generated `.xlsm` file against a manually
prepared ground-truth Excel to verify pipeline accuracy.

---

## The Core Problem

Our Excel generator (`excel_generator.py`) uses openpyxl with `keep_vba=True` to fill the
INPUT SHEET of `CMA.xlsm`. The resulting file must be compared against `CMA Dynamic 23082025.xls`
(the CA-prepared ground truth). The comparison must:

1. Read values from specific rows/columns (known from `cma_field_rows.py` + `year_columns.py`)
2. Handle cells that contain formulas — we want the **computed result**, not the formula string
3. Treat floating point numbers with tolerance (financial amounts in lakhs)
4. Report exactly which cells differ, with expected vs. actual and % error

---

## Library Comparison

### 1. openpyxl (already in project — `openpyxl>=3.1.0`)

**Supports .xlsm:** Yes — `load_workbook(path, keep_vba=True)` reads macro-enabled files.

**Formula handling — the critical limitation:**

openpyxl reads the **formula string**, not the computed value, unless the file was saved with
cached values. When Excel or LibreOffice saves a file, it writes the last computed value into
each formula cell alongside the formula (called the "cached value"). openpyxl can read cached
values with `data_only=True`:

```python
import openpyxl

wb = openpyxl.load_workbook("CMA_output.xlsm", data_only=True, keep_vba=True)
ws = wb["INPUT SHEET"]

cell = ws["B22"]
print(cell.value)   # Returns the cached numeric value, or None if never computed
print(type(cell.value))  # int, float, or None
```

**Critical caveat:** `data_only=True` returns `None` for formula cells if the file was saved
without first computing formulas (e.g., saved programmatically by openpyxl itself without
opening in Excel). A file saved by our `ExcelGenerator` will have `None` in formula cells
because openpyxl does not execute VBA or worksheet formulas.

**Practical meaning for our project:**

- The **generated file** (written by openpyxl): `data_only=True` returns actual numeric values
  for cells we wrote (row 22, column B, etc.) — because we wrote a float, not a formula.
- The **ground-truth file** (CMA Dynamic 23082025.xls, opened and saved by a human in Excel):
  `data_only=True` returns cached numeric values — because Excel computed and cached them.

This means openpyxl `data_only=True` works for our comparison use case because:
- We write floats into the INPUT SHEET (not formulas)
- The CA-prepared file was saved by Excel, so cached values are populated

**Reading .xls files:** openpyxl does NOT read `.xls` (Excel 97-2003). The ground truth
`CMA Dynamic 23082025.xls` is an `.xls` file — requires xlrd.

---

### 2. xlrd (already in project — `xlrd>=2.0.1`)

**Supports .xlsm:** No. xlrd 2.0+ removed support for all formats except `.xls` (Excel
97-2003). For `.xlsm` files, xlrd raises `XLRDError: Excel xlsx file; not supported`.

**Supports .xls:** Yes — this is the only format xlrd 2.x supports.

**Formula handling:** xlrd reads the **cached/computed value** from `.xls` files automatically.
There is no `data_only` mode — you always get the numeric result, never the formula string.

```python
import xlrd

wb = xlrd.open_workbook("CMA_Dynamic_23082025.xls")
ws = wb.sheet_by_name("INPUT SHEET")

# xlrd uses 0-based row/col indices
row_22_col_b = ws.cell_value(rowx=21, colx=1)  # row 22 = index 21, col B = index 1
print(row_22_col_b)  # 12345678.0  (numeric value)
```

**Cell type detection:**

```python
import xlrd

ws = wb.sheet_by_name("INPUT SHEET")
cell = ws.cell(21, 1)

if cell.ctype == xlrd.XL_CELL_NUMBER:
    value = cell.value  # float
elif cell.ctype == xlrd.XL_CELL_EMPTY:
    value = None
elif cell.ctype == xlrd.XL_CELL_TEXT:
    value = cell.value  # str
```

**Verdict for ground truth:** xlrd is the right tool to read `.xls` ground truth files.

---

### 3. xlwings

**Supports .xlsm:** Yes — xlwings controls a running Excel instance (on Windows/macOS) and
can read computed values from any formula cell, even if the file was never saved with caches.

**Formula handling:** xlwings actually opens Excel and reads the live computed value:

```python
import xlwings as xw

app = xw.App(visible=False)
wb = app.books.open("CMA_output.xlsm")
ws = wb.sheets["INPUT SHEET"]

# Row 22, Column B (xlwings uses 1-based by default)
value = ws.range("B22").value
print(value)  # 12345678.0  — Excel computed this live
wb.close()
app.quit()
```

**Advantages:**
- Works even when files were never saved with cached values
- Can run macros before reading (important if macros auto-compute totals)
- Reads merged cell values correctly

**Disadvantages:**
- Requires Excel installed (Windows or macOS only — not available in Docker/Linux)
- Slow — opens a full Excel process (~5-10 seconds startup)
- Not suitable for CI/CD pipelines running in Docker containers

**Verdict:** xlwings is powerful on a local Windows machine (like the CA's laptop) but unusable
in our Docker backend.

---

### 4. pyxlsb

**Supports:** `.xlsb` (Excel Binary Workbook) only. Not relevant for our `.xlsm` / `.xls` files.

---

### 5. pandas (with openpyxl or xlrd engine)

pandas does not add capability over openpyxl/xlrd — it uses them as engines. For targeted
cell-by-cell comparison, pandas is heavier than needed. Useful only if comparing entire sheets
as DataFrames.

```python
import pandas as pd

# Read specific sheet with openpyxl engine
df_generated = pd.read_excel("generated.xlsm", sheet_name="INPUT SHEET", engine="openpyxl")
df_truth = pd.read_excel("CMA_Dynamic.xls", sheet_name="INPUT SHEET", engine="xlrd")
```

**Note:** `read_excel` with openpyxl still suffers the same `data_only` limitation — formula
cells in the generated file will be populated with the values we wrote (fine), but formula cells
in the template that we did NOT overwrite will return their formula strings.

---

### 6. Dedicated Excel diff tools

| Tool | How it works | Formula values | CLI | Output format |
|------|-------------|----------------|-----|---------------|
| `xlsx-diff` (npm) | Node.js, text diff | No — formula strings | Yes | Text |
| `pyxlcompare` | openpyxl-based | No — formula strings | Yes | HTML report |
| `xlcompare` (commercial) | COM-based | Yes (Excel required) | Yes | Excel |
| `openpyxl-diff` | Pure openpyxl | No — formula strings | No | Python dict |

**Verdict:** No existing open-source tool handles the formula-value problem in a
Docker-compatible way. A custom comparison using openpyxl + xlrd is the right approach.

---

## The Formula Value Problem — Full Solution

Our generated `.xlsm` is written by openpyxl (no formula evaluation happens). The INPUT SHEET
cells we write are numeric values — no formulas. The cells we do NOT write (totals, subtotals)
may contain formulas from the template that openpyxl preserves but does not evaluate.

**Solution: compare only the cells we actually write.**

We know exactly which cells we write from `cma_field_rows.py` and `year_columns.py`. Our
comparison should ONLY check those cells — not formula-computed subtotals or totals.

```python
# The cells we write = ALL_FIELD_TO_ROW × YEAR_TO_COLUMN
from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.mappings.year_columns import YEAR_TO_COLUMN

COMPARE_CELLS = [
    (field, row, year, col)
    for field, row in ALL_FIELD_TO_ROW.items()
    for year, col in YEAR_TO_COLUMN.items()
]
# 89 fields × up to 4 years = up to 356 cells to compare
```

This avoids the formula evaluation problem entirely.

---

## Recommended Approach for Our Project

**For reading the generated `.xlsm` file:** Use openpyxl with `data_only=True, keep_vba=True`.
All cells we wrote contain floats — openpyxl reads them correctly.

**For reading the ground-truth `.xls` file:** Use xlrd. It automatically returns computed
numeric values from `.xls` files.

**Do NOT use xlwings in the Docker backend.** It requires a running Excel instance. It is
acceptable on the developer's local Windows machine for manual spot-checks.

**Do NOT compare formula cells** (subtotals, totals). Compare only the input cells defined in
`cma_field_rows.py` × `year_columns.py`.

---

## Cell-by-Cell Comparison Code

```python
"""
excel_comparator.py — Compare generated CMA.xlsm against ground-truth .xls

Works entirely with openpyxl (for .xlsm) and xlrd (for .xls).
No Excel installation required. Docker-compatible.
"""
from __future__ import annotations

import openpyxl
import xlrd

from app.mappings.cma_field_rows import ALL_FIELD_TO_ROW
from app.mappings.year_columns import YEAR_TO_COLUMN

SHEET_NAME = "INPUT SHEET"
TOLERANCE = 0.01  # 1% relative tolerance for financial amounts


def read_generated_xlsm(path: str) -> dict[tuple[int, str], float | None]:
    """Read INPUT SHEET from openpyxl-generated .xlsm.

    Returns {(row, col_letter): value_or_none}
    """
    wb = openpyxl.load_workbook(path, data_only=True, keep_vba=True)
    ws = wb[SHEET_NAME]

    values = {}
    for field, row in ALL_FIELD_TO_ROW.items():
        for year, col in YEAR_TO_COLUMN.items():
            cell = ws.cell(row=row, column=openpyxl.utils.column_index_from_string(col))
            raw = cell.value
            # openpyxl may return int, float, str, or None
            if isinstance(raw, (int, float)) and raw != 0:
                values[(row, col)] = float(raw)
            else:
                values[(row, col)] = None
    wb.close()
    return values


def read_ground_truth_xls(path: str) -> dict[tuple[int, str], float | None]:
    """Read INPUT SHEET from xlrd (ground-truth .xls prepared by CA).

    Returns {(row, col_letter): value_or_none}
    xlrd uses 0-based row/col; openpyxl row numbers are 1-based.
    """
    wb = xlrd.open_workbook(path)
    # Try both common sheet names
    try:
        ws = wb.sheet_by_name(SHEET_NAME)
    except xlrd.biffh.XLRDError:
        ws = wb.sheet_by_index(0)

    # Build col letter → xlrd 0-based col index
    col_map = {col: openpyxl.utils.column_index_from_string(col) - 1
               for col in YEAR_TO_COLUMN.values()}

    values = {}
    for field, row in ALL_FIELD_TO_ROW.items():
        xlrd_row = row - 1  # convert 1-based to 0-based
        if xlrd_row >= ws.nrows:
            continue
        for year, col in YEAR_TO_COLUMN.items():
            xlrd_col = col_map[col]
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

## Library Decision Matrix

| Requirement | openpyxl | xlrd | xlwings |
|-------------|----------|------|---------|
| Read .xlsm | Yes | No | Yes |
| Read .xls | No | Yes | Yes |
| Get computed formula values | No (data_only reads cache) | Yes (auto) | Yes (live Excel) |
| Docker/Linux compatible | Yes | Yes | No |
| Already in requirements.txt | Yes | Yes | No |
| Speed | Fast | Fast | Slow |

---

## Recommended for Our Project

Use **openpyxl (data_only=True)** for the generated `.xlsm` and **xlrd** for the `.xls`
ground-truth. Both are already in `backend/requirements.txt`. No new dependencies needed.

The comparison script must be limited to cells defined in `ALL_FIELD_TO_ROW` ×
`YEAR_TO_COLUMN` — these are the cells the generator writes, and they contain floats (not
formulas), so `data_only=True` works correctly.

Do not try to compare subtotal rows or total rows — those contain Excel formulas which
openpyxl cannot evaluate without running Excel.
