import pikepdf
from io import BytesIO


def get_page_count(pdf_bytes: bytes) -> int:
    """Return total page count of a PDF."""
    with pikepdf.Pdf.open(BytesIO(pdf_bytes)) as pdf:
        return len(pdf.pages)


def parse_page_ranges(range_str: str, total_pages: int) -> list[int]:
    """Parse '1-3, 7, 10-15' into sorted list of pages to REMOVE (1-indexed).

    Handles: empty string, invalid ranges, out-of-bounds, duplicates.
    Returns only valid page numbers within [1, total_pages].
    """
    if not range_str or not range_str.strip():
        return []
    to_remove = set()
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                s, e = int(start.strip()), int(end.strip())
                to_remove.update(range(max(1, s), min(e, total_pages) + 1))
            except ValueError:
                continue
        else:
            try:
                p = int(part.strip())
                if 1 <= p <= total_pages:
                    to_remove.add(p)
            except ValueError:
                continue
    return sorted(to_remove)


def pages_to_keep(range_str: str, total_pages: int) -> list[int]:
    """Return 1-indexed list of pages to KEEP after removing specified pages."""
    removing = set(parse_page_ranges(range_str, total_pages))
    return [p for p in range(1, total_pages + 1) if p not in removing]


def remove_pages(pdf_bytes: bytes, keep_pages: list[int]) -> bytes:
    """Create new PDF with only the specified pages (1-indexed).

    Uses pikepdf for lossless page removal with automatic dead object cleanup.
    """
    with pikepdf.Pdf.open(BytesIO(pdf_bytes)) as pdf:
        total = len(pdf.pages)
        keep_indices = sorted(set(p - 1 for p in keep_pages if 1 <= p <= total))
        to_delete = [i for i in range(total) if i not in keep_indices]
        for idx in reversed(to_delete):
            del pdf.pages[idx]
        output = BytesIO()
        pdf.save(output)
        return output.getvalue()
