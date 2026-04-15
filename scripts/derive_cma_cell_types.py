"""Derive cma_cell_types.json from cma_cell_map.json + field_rows mappings.

Phase 0 of the cell-type-awareness prompt rework. Classifies every INPUT SHEET
row as one of:

    META         rows 11-15 (FY, Currency, Units, Auditors, Opinion)
    YELLOW       is_formula_row == true (auto-computed — never write here)
    BLANK        empty label (spacer rows)
    NOTE_ROW     parenthetical label like "(o/s bill discounting...)"
    BLUE         row listed in PNL_FIELD_TO_ROW or BS_FIELD_TO_ROW (valid target)
    WHITE_HEADER everything else (section titles like "Sales", "Income")

Classification order matters — first match wins.

Output schema:

    {
      "generated_from": [...],
      "type_counts": {"BLUE": 118, "YELLOW": 56, ...},
      "rows": {"21": {"label": "Sales", "type": "WHITE_HEADER"}, ...},
      "agents": {
        "pl_income": {
          "section_tree": "R17 [HEADER ]  Profit and Loss\n...",
          "valid_rows": [22, 23, 25, 29, 30, 31, 32, 33, 34]
        },
        ...
      }
    }

Usage:
    python scripts/derive_cma_cell_types.py
    python scripts/derive_cma_cell_types.py --output custom/path.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CELL_MAP_PATH = REPO_ROOT / "DOCS" / "cma_cell_map.json"
DEFAULT_OUTPUT = REPO_ROOT / "DOCS" / "cma_cell_types.json"

# Make `app.mappings.cma_field_rows` importable.
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.mappings.cma_field_rows import PNL_FIELD_TO_ROW  # noqa: E402

try:
    from app.mappings.cma_field_rows import BS_FIELD_TO_ROW  # noqa: E402
except ImportError:
    BS_FIELD_TO_ROW = {}


META_ROWS = {11, 12, 13, 14, 15}

AGENT_RANGES = {
    "pl_income":    (17, 35),
    "pl_expense":   (38, 109),
    "bs_liability": (110, 160),
    "bs_asset":     (161, 262),
}

NOTE_ROW_LABELS = {"(o/s bill discounting balance to be included)"}

TAG_BY_TYPE = {
    "BLUE":         "TARGET ",
    "YELLOW":       "FORMULA",
    "WHITE_HEADER": "HEADER ",
    "NOTE_ROW":     "NOTE   ",
    "META":         "META   ",
}


def _is_parenthetical(label: str) -> bool:
    """True if label is wrapped in parentheses (an instructional note row)."""
    stripped = label.strip()
    return stripped.startswith("(") and stripped.endswith(")") and len(stripped) >= 2


def classify_row(row_num: int, entry: dict, valid_targets: set[int]) -> str:
    """Classify a single row. Order matters: META → YELLOW → BLANK → NOTE → BLUE → WHITE_HEADER."""
    label = entry.get("label", "") or ""

    if row_num in META_ROWS:
        return "META"
    if entry.get("is_formula_row"):
        return "YELLOW"
    if not label.strip():
        return "BLANK"
    if label in NOTE_ROW_LABELS or _is_parenthetical(label):
        return "NOTE_ROW"
    if row_num in valid_targets:
        return "BLUE"
    return "WHITE_HEADER"


def build_section_tree(rows: dict[str, dict], start: int, end: int) -> str:
    """Render an aligned tree of every non-BLANK row in [start, end]."""
    lines: list[str] = []
    for r in range(start, end + 1):
        entry = rows.get(str(r))
        if entry is None:
            continue
        row_type = entry["type"]
        if row_type == "BLANK":
            continue
        tag = TAG_BY_TYPE.get(row_type, row_type[:7].ljust(7))
        lines.append(f"R{r:<3} [{tag}]  {entry['label']}")
    return "\n".join(lines)


def derive(cell_map: dict) -> dict:
    valid_targets = set(PNL_FIELD_TO_ROW.values()) | set(BS_FIELD_TO_ROW.values())

    rows: dict[str, dict] = {}
    type_counts: dict[str, int] = {
        "BLUE": 0, "YELLOW": 0, "WHITE_HEADER": 0,
        "NOTE_ROW": 0, "BLANK": 0, "META": 0,
    }

    for row_key in sorted(cell_map.keys(), key=int):
        row_num = int(row_key)
        entry = cell_map[row_key]
        row_type = classify_row(row_num, entry, valid_targets)
        rows[row_key] = {
            "label": entry.get("label", "") or "",
            "type": row_type,
        }
        type_counts[row_type] += 1

    agents: dict[str, dict] = {}
    for agent_key, (start, end) in AGENT_RANGES.items():
        valid_rows = sorted(
            int(k) for k, v in rows.items()
            if v["type"] == "BLUE" and start <= int(k) <= end
        )
        section_tree = build_section_tree(rows, start, end)
        agents[agent_key] = {
            "section_tree": section_tree,
            "valid_rows": valid_rows,
        }

    return {
        "generated_from": [
            "DOCS/cma_cell_map.json",
            "backend/app/mappings/cma_field_rows.py",
        ],
        "type_counts": type_counts,
        "rows": rows,
        "agents": agents,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", "-o",
        default=str(DEFAULT_OUTPUT),
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    with open(CELL_MAP_PATH, encoding="utf-8") as f:
        cell_map = json.load(f)

    result = derive(cell_map)

    # Round-trip validation.
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    json.loads(payload)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")

    print(f"Wrote {out_path}")
    print(f"type_counts: {result['type_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
