"""
Import CMA reference mappings from DOCS/CMA classification.xls into Supabase.

Run from project root:
    python scripts/import_reference_data.py

Requires: xlrd, supabase, python-dotenv
Uses service_role key to bypass RLS (seed script, not production code).
"""

import os
import sys
from pathlib import Path

import xlrd
from dotenv import load_dotenv
from supabase import create_client

# ── Setup ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
DOCS_PATH = ROOT / "DOCS" / "CMA classification.xls"

# ── Parse Excel ───────────────────────────────────────────────────────────────

SHEET_MAP = {
    "Balance Sheet": "balance_sheet",
    "Profit and Loss": "profit_and_loss",
}


def parse_sheet(workbook: xlrd.Book, sheet_name: str, source_key: str) -> list[dict]:
    sh = workbook.sheet_by_name(sheet_name)
    rows = []
    for r in range(sh.nrows):
        sr_no_raw = sh.cell_value(r, 0)
        item_name = str(sh.cell_value(r, 1)).strip()

        # Only process rows where Sr.No. is a positive number and item name exists
        if not (isinstance(sr_no_raw, float) and sr_no_raw > 0 and item_name):
            continue

        cma_form_item = str(sh.cell_value(r, 2)).strip()
        broad_classification = str(sh.cell_value(r, 3)).strip()
        remarks_raw = sh.cell_value(r, 4)
        remarks = str(remarks_raw).strip() if remarks_raw else None

        rows.append(
            {
                "source_sheet": source_key,
                "sr_no": sr_no_raw,
                "item_name": item_name,
                "cma_form_item": cma_form_item,
                "broad_classification": broad_classification,
                "remarks": remarks or None,
                # cma_input_row populated by classification pipeline via cma_field_rows.py
                "cma_input_row": None,
            }
        )
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    if not DOCS_PATH.exists():
        print(f"ERROR: {DOCS_PATH} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {DOCS_PATH}...")
    wb = xlrd.open_workbook(str(DOCS_PATH))

    all_rows: list[dict] = []
    for sheet_name, source_key in SHEET_MAP.items():
        rows = parse_sheet(wb, sheet_name, source_key)
        print(f"  {sheet_name}: {len(rows)} items")
        all_rows.extend(rows)

    print(f"Total: {len(all_rows)} items to import")

    # Connect with service role key (bypasses RLS)
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    # Check existing count
    existing = client.table("cma_reference_mappings").select("id", count="exact").execute()
    if existing.count and existing.count > 0:
        print(f"WARNING: Table already has {existing.count} rows. Skipping import.")
        print("To re-import, delete existing rows first.")
        return

    # Batch insert in chunks of 100
    BATCH_SIZE = 100
    inserted = 0
    for i in range(0, len(all_rows), BATCH_SIZE):
        batch = all_rows[i : i + BATCH_SIZE]
        result = client.table("cma_reference_mappings").insert(batch).execute()
        inserted += len(result.data)
        print(f"  Inserted rows {i + 1}–{i + len(batch)} ({inserted} total)")

    print(f"\nDone. {inserted} reference mappings imported.")


if __name__ == "__main__":
    main()
