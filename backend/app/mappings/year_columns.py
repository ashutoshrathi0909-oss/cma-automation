"""Maps financial year to CMA INPUT SHEET column letter.

CMA INPUT SHEET layout (row 8):
  Column B = first (earliest) year, C = B+1, D = B+2, ...

The base year is determined DYNAMICALLY from the documents in each
report — ``build_year_map(financial_years)`` returns a dict mapping
each year to its column letter, starting from column B for the
earliest year.
"""

from __future__ import annotations

# Column letters indexed from B (col index 2) onward
_COLUMN_LETTERS = "BCDEFGHIJKLM"


def get_year_column(year: int, base_year: int) -> str | None:
    """Return the column letter for *year* given a *base_year* in column B.

    Returns None if the year falls outside the supported range (B–M).
    """
    offset = year - base_year
    if 0 <= offset < len(_COLUMN_LETTERS):
        return _COLUMN_LETTERS[offset]
    return None


def build_year_map(financial_years: list[int]) -> dict[int, str]:
    """Build a {year: column_letter} mapping from actual document years.

    The earliest year maps to column B, next to C, etc.
    Returns empty dict if no years provided.
    """
    if not financial_years:
        return {}
    base = min(financial_years)
    return {
        yr: col
        for yr in sorted(set(financial_years))
        if (col := get_year_column(yr, base)) is not None
    }
