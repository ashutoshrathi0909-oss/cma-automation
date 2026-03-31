#!/usr/bin/env python3
"""
Parse an .xls workbook into JSON (using xlrd for legacy .xls files).

Usage:
    python parse_xls.py "Company File.xls" --output company_sheets.json
    python parse_xls.py "Company File.xls"  # prints to stdout

Requires: pip install xlrd
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import xlrd
except ImportError:
    print("Error: xlrd not installed. Run: pip install xlrd", file=sys.stderr)
    sys.exit(1)


def parse_sheet(ws):
    """Extract all data from a worksheet."""
    rows = []
    for row_idx in range(ws.nrows):
        row_data = []
        for col_idx in range(ws.ncols):
            cell = ws.cell(row_idx, col_idx)
            ctype = cell.ctype
            value = cell.value

            if ctype == xlrd.XL_CELL_EMPTY:
                row_data.append(None)
            elif ctype == xlrd.XL_CELL_NUMBER:
                # Convert floats that are whole numbers to int for cleaner output
                if value == int(value):
                    row_data.append(int(value))
                else:
                    row_data.append(value)
            elif ctype == xlrd.XL_CELL_TEXT:
                row_data.append(str(value))
            elif ctype == xlrd.XL_CELL_BOOLEAN:
                row_data.append(bool(value))
            elif ctype == xlrd.XL_CELL_DATE:
                # Return as string for JSON safety
                try:
                    dt = xlrd.xldate_as_datetime(value, ws.book.datemode)
                    row_data.append(dt.strftime("%Y-%m-%d"))
                except Exception:
                    row_data.append(str(value))
            else:
                row_data.append(None)
        rows.append(row_data)

    return rows


def parse_workbook(filepath):
    """Parse entire workbook into a dict of sheet_name -> rows."""
    wb = xlrd.open_workbook(filepath)

    result = {
        "file": Path(filepath).name,
        "sheets": {}
    }

    for sheet_name in wb.sheet_names():
        ws = wb.sheet_by_name(sheet_name)
        rows = parse_sheet(ws)

        # Skip completely empty sheets
        if not any(any(cell is not None for cell in row) for row in rows):
            continue

        # Trim trailing empty rows
        while rows and all(cell is None for cell in rows[-1]):
            rows.pop()

        result["sheets"][sheet_name] = {
            "row_count": len(rows),
            "col_count": ws.ncols,
            "data": rows
        }

    return result


def main():
    parser = argparse.ArgumentParser(description="Parse .xls workbook to JSON")
    parser.add_argument("file", help="Path to .xls file")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = parse_workbook(args.file)

    # Summary
    print(f"Parsed: {result['file']}", file=sys.stderr)
    for name, sheet in result["sheets"].items():
        print(f"  Sheet '{name}': {sheet['row_count']} rows x {sheet['col_count']} cols", file=sys.stderr)

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
