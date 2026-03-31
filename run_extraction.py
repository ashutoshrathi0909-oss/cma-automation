"""
Agent 3: Extraction Pipeline for Dynamic Air Engineering
Uploads all documents, triggers extraction, polls for completion.
"""
import requests
import json
import time
import sys

BASE = "http://localhost:8000"
HEADERS = {
    "X-User-Id": "00000000-0000-0000-0000-000000000001",
    "X-User-Role": "admin"
}

CLIENT_ID = "2640855e-9676-4318-a274-8e911b7fac5e"
BASE_PATH = "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/DOCS/Financials"

MIME_TYPES = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
}

# Documents to upload: (file_path, financial_year, document_type, nature, display_name, target_items)
DOCUMENTS = [
    (
        f"{BASE_PATH}/FY_22/Financials/BS-Dynamic 2022 - Companies Act.xlsx",
        2022,
        "combined_financial_statement",
        "audited",
        "BS-Dynamic 2022 - Companies Act.xlsx",
        20,
    ),
    (
        f"{BASE_PATH}/FY_22/Financials/Notes to Financials.pdf",
        2022,
        "notes_to_accounts",
        "audited",
        "Notes to Financials.pdf",
        15,
    ),
    (
        f"{BASE_PATH}/FY_22/Financials/ITR BS P&L.pdf",
        2022,
        "combined_financial_statement",
        "audited",
        "ITR BS P&L.pdf",
        15,
    ),
    (
        f"{BASE_PATH}/FY-23/ITR PL & BS.pdf",
        2023,
        "combined_financial_statement",
        "audited",
        "ITR PL & BS.pdf",
        20,
    ),
    (
        f"{BASE_PATH}/FY-23/Notes..pdf",
        2023,
        "notes_to_accounts",
        "audited",
        "Notes..pdf",
        15,
    ),
    (
        f"{BASE_PATH}/FY-24/Audited Financials FY-2024 (1).pdf",
        2024,
        "combined_financial_statement",
        "audited",
        "Audited Financials FY-2024 (1).pdf",
        50,  # hard gate
    ),
    (
        f"{BASE_PATH}/FY2025/Provisional financial 31.03.25 (3).xlsx",
        2025,
        "combined_financial_statement",
        "provisional",
        "Provisional financial 31.03.25 (3).xlsx",
        20,
    ),
]


def upload_document(file_path, financial_year, doc_type, nature, display_name):
    print(f"\n{'='*60}")
    print(f"Uploading: {display_name}")
    print(f"  Year: {financial_year}, Type: {doc_type}, Nature: {nature}")

    ext = display_name.rsplit(".", 1)[-1].lower() if "." in display_name else "bin"
    mime = MIME_TYPES.get(ext, "application/octet-stream")

    with open(file_path, "rb") as f:
        file_bytes = f.read()
    print(f"  File size: {len(file_bytes):,} bytes")

    resp = requests.post(
        f"{BASE}/api/documents/",
        headers=HEADERS,
        data={
            "client_id": CLIENT_ID,
            "document_type": doc_type,
            "financial_year": str(financial_year),
            "nature": nature,
        },
        files={"file": (display_name, file_bytes, mime)}
    )

    if resp.status_code != 201:
        print(f"  ERROR uploading: {resp.status_code} {resp.text[:300]}")
        return None

    doc = resp.json()
    doc_id = doc["id"]
    print(f"  Uploaded OK -> doc_id: {doc_id}")
    return doc_id


def trigger_extraction(doc_id):
    resp = requests.post(
        f"{BASE}/api/documents/{doc_id}/extract",
        headers=HEADERS
    )
    print(f"  Extraction triggered: {resp.status_code}")
    if resp.status_code not in (200, 201, 202):
        print(f"  ERROR: {resp.text[:200]}")
    return resp.status_code in (200, 201, 202)


def poll_extraction(doc_id, timeout_minutes=15):
    start = time.time()
    last_status = None
    while time.time() - start < timeout_minutes * 60:
        resp = requests.get(f"{BASE}/api/documents/{doc_id}", headers=HEADERS)
        if resp.status_code != 200:
            print(f"  Error fetching doc: {resp.status_code}")
            time.sleep(10)
            continue
        doc = resp.json()
        status = doc.get("extraction_status", "unknown")
        elapsed = int(time.time() - start)
        if status != last_status:
            print(f"  [{elapsed}s] Status changed: {status}")
            last_status = status
        else:
            print(f"  [{elapsed}s] Still: {status}")
        if status in ("extracted", "verified", "failed", "error"):
            return status, int(time.time() - start)
        time.sleep(15)
    return "timeout", int(time.time() - start)


def fetch_items(doc_id):
    resp = requests.get(f"{BASE}/api/documents/{doc_id}/items", headers=HEADERS)
    if resp.status_code != 200:
        print(f"  Error fetching items: {resp.status_code} {resp.text[:100]}")
        return []
    items = resp.json()
    return items


def main():
    results = []
    doc_ids = []
    fy24_doc_id = None
    fy24_items = []

    for i, (file_path, fy, doc_type, nature, display_name, target) in enumerate(DOCUMENTS):
        print(f"\n[{i+1}/7] Processing: {display_name} (FY{fy})")

        # Upload
        doc_id = upload_document(file_path, fy, doc_type, nature, display_name)
        if doc_id is None:
            results.append({
                "name": display_name,
                "year": fy,
                "doc_id": None,
                "items": 0,
                "status": "upload_failed",
                "time": 0,
                "target": target,
                "pass": False
            })
            doc_ids.append(None)
            continue

        doc_ids.append(doc_id)

        if fy == 2024 and doc_type == "combined_financial_statement":
            fy24_doc_id = doc_id

        # Trigger extraction
        ok = trigger_extraction(doc_id)
        if not ok:
            results.append({
                "name": display_name,
                "year": fy,
                "doc_id": doc_id,
                "items": 0,
                "status": "trigger_failed",
                "time": 0,
                "target": target,
                "pass": False
            })
            continue

        # Poll for completion (longer timeout for FY24 Vision OCR)
        timeout_min = 15 if (fy == 2024 and "Audited" in display_name) else 10
        status, elapsed = poll_extraction(doc_id, timeout_minutes=timeout_min)

        # Fetch items
        items = fetch_items(doc_id)
        item_count = len(items)

        passed = item_count >= target
        print(f"  RESULT: {item_count} items (target>={target}): {'PASS' if passed else 'FAIL'}")
        print(f"  Status: {status}, Time: {elapsed}s")

        result = {
            "name": display_name,
            "year": fy,
            "doc_id": doc_id,
            "items": item_count,
            "status": status,
            "time": elapsed,
            "target": target,
            "pass": passed,
            "item_list": items
        }
        results.append(result)

        if fy == 2024 and doc_type == "combined_financial_statement":
            fy24_items = items
            print(f"\n  *** FY24 VISION OCR CHECK ***")
            print(f"  Items: {item_count} (hard gate: >=50): {'PASS' if item_count >= 50 else 'HARD GATE FAILED!'}")

            sections = {}
            for item in items:
                s = item.get('section', 'unknown')
                sections[s] = sections.get(s, 0) + 1
            print(f"  Sections: {sections}")
            print(f"  Sample items (first 10):")
            for item in items[:10]:
                print(f"    {item.get('description', 'N/A')}: {item.get('amount', 'N/A')}")

    # Print summary
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    total_items = sum(r.get("items", 0) for r in results)

    for r in results:
        gate = "PASS" if r.get("pass") else "FAIL"
        items = r.get("items", 0)
        name = r.get("name", "")[:45]
        status = r.get("status", "")
        elapsed = r.get("time", 0)
        target = r.get("target", 0)
        print(f"[{gate}] {name:<45} | FY{r.get('year')} | {items:>4} items (>={target}) | {status:<12} | {elapsed}s")

    print(f"\nTotal items: {total_items} (soft gate: >=135)")
    print(f"CLIENT_ID: {CLIENT_ID}")
    print(f"Doc IDs: {doc_ids}")
    if fy24_doc_id:
        print(f"FY24 Doc ID: {fy24_doc_id}")

    all_passed = all(r.get("pass", False) for r in results)
    fy24_items_count = len(fy24_items)
    hard_gate = fy24_items_count >= 50
    soft_gate = total_items >= 135

    print(f"\nGATES:")
    print(f"  Hard gate (FY24 >=50): {'PASS' if hard_gate else 'FAIL'} ({fy24_items_count})")
    print(f"  Soft gate (Total >=135): {'PASS' if soft_gate else 'WARN'} ({total_items})")

    return results, doc_ids, fy24_doc_id, fy24_items, total_items


if __name__ == "__main__":
    results, doc_ids, fy24_doc_id, fy24_items, total_items = main()

    # Save as JSON for reference
    output = {
        "client_id": CLIENT_ID,
        "doc_ids": doc_ids,
        "fy24_doc_id": fy24_doc_id,
        "results": [{k: v for k, v in r.items() if k != "item_list"} for r in results]
    }
    import os
    os.makedirs("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/dynamic", exist_ok=True)
    with open("C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/dynamic/extraction_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nSaved to test-results/dynamic/extraction_results.json")
