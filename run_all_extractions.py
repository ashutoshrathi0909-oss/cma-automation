"""
Agent 3: Run extraction for all remaining documents.
FY22 Excel (doc1) and FY22 Notes (doc2) already done.
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

# Remaining documents to process
REMAINING_DOCS = [
    # (file_path, fy, doc_type, nature, display_name, target, timeout_min)
    (
        f"{BASE_PATH}/FY_22/Financials/ITR BS P&L.pdf",
        2022, "combined_financial_statement", "audited",
        "ITR BS P&L.pdf", 15, 10
    ),
    (
        f"{BASE_PATH}/FY-23/ITR PL & BS.pdf",
        2023, "combined_financial_statement", "audited",
        "ITR PL & BS.pdf", 20, 10
    ),
    (
        f"{BASE_PATH}/FY-23/Notes..pdf",
        2023, "notes_to_accounts", "audited",
        "Notes..pdf", 15, 15
    ),
    (
        f"{BASE_PATH}/FY-24/Audited Financials FY-2024 (1).pdf",
        2024, "combined_financial_statement", "audited",
        "Audited Financials FY-2024 (1).pdf", 50, 20  # HARD GATE
    ),
    (
        f"{BASE_PATH}/FY2025/Provisional financial 31.03.25 (3).xlsx",
        2025, "combined_financial_statement", "provisional",
        "Provisional financial 31.03.25 (3).xlsx", 20, 5
    ),
]


def upload(file_path, fy, doc_type, nature, display_name):
    ext = display_name.rsplit(".", 1)[-1].lower()
    mime = MIME_TYPES.get(ext, "application/octet-stream")
    with open(file_path, "rb") as f:
        data = f.read()
    print(f"  Uploading {display_name} ({len(data):,} bytes)...")
    resp = requests.post(
        f"{BASE}/api/documents/",
        headers=HEADERS,
        data={"client_id": CLIENT_ID, "document_type": doc_type, "financial_year": str(fy), "nature": nature},
        files={"file": (display_name, data, mime)}
    )
    if resp.status_code != 201:
        print(f"  UPLOAD ERROR: {resp.status_code} {resp.text[:200]}")
        return None
    doc_id = resp.json()["id"]
    print(f"  Uploaded: {doc_id}")
    return doc_id


def trigger(doc_id):
    resp = requests.post(f"{BASE}/api/documents/{doc_id}/extract", headers=HEADERS)
    print(f"  Trigger: {resp.status_code}")
    return resp.status_code in (200, 201, 202)


def poll(doc_id, timeout_min=10):
    start = time.time()
    last = None
    timeout = timeout_min * 60
    while time.time() - start < timeout:
        resp = requests.get(f"{BASE}/api/documents/?client_id={CLIENT_ID}", headers=HEADERS)
        if resp.status_code != 200:
            time.sleep(10)
            continue
        docs = resp.json()
        doc = next((d for d in docs if d["id"] == doc_id), None)
        if not doc:
            time.sleep(10)
            continue
        status = doc.get("extraction_status", "unknown")
        elapsed = int(time.time() - start)
        if status != last:
            print(f"  [{elapsed}s] {status}")
            last = status
        if status in ("extracted", "verified", "failed"):
            return status, elapsed
        time.sleep(20)
    return "timeout", int(time.time() - start)


def fetch_items(doc_id):
    resp = requests.get(f"{BASE}/api/documents/{doc_id}/items", headers=HEADERS)
    if resp.status_code != 200:
        print(f"  Items error: {resp.status_code}")
        return []
    return resp.json()


results = []
new_doc_ids = []

for file_path, fy, doc_type, nature, display_name, target, timeout_min in REMAINING_DOCS:
    print(f"\n{'='*65}")
    print(f"Processing: {display_name} (FY{fy})")

    start_wall = time.time()
    doc_id = upload(file_path, fy, doc_type, nature, display_name)
    if not doc_id:
        results.append({"name": display_name, "year": fy, "doc_id": None,
                        "items": 0, "status": "upload_failed", "time": 0, "target": target})
        new_doc_ids.append(None)
        continue

    new_doc_ids.append(doc_id)

    if not trigger(doc_id):
        results.append({"name": display_name, "year": fy, "doc_id": doc_id,
                        "items": 0, "status": "trigger_failed", "time": 0, "target": target})
        continue

    status, elapsed = poll(doc_id, timeout_min=timeout_min)
    items = fetch_items(doc_id)
    n = len(items)
    gate = "PASS" if n >= target else "FAIL"
    total_wall = int(time.time() - start_wall)

    print(f"  [{gate}] {n} items (target>={target}), status={status}, time={elapsed}s")

    results.append({
        "name": display_name,
        "year": fy,
        "doc_id": doc_id,
        "items": n,
        "status": status,
        "time": elapsed,
        "target": target,
        "pass": n >= target,
        "items_data": items
    })

    if fy == 2024 and "Audited" in display_name:
        FY24_DOC_ID = doc_id
        FY24_ITEMS = items
        print(f"\n  *** FY24 HARD GATE: {n} items (need >=50) ***")
        if n < 50:
            print("  !!! HARD GATE FAILED !!!")
        else:
            print("  *** HARD GATE PASSED ***")

        sections = {}
        for item in items:
            s = item.get("section", "unknown") or "unknown"
            sections[s] = sections.get(s, 0) + 1
        print(f"  Sections: {sections}")
        print(f"  First 10 items:")
        for item in items[:10]:
            print(f"    {item.get('description', 'N/A')}: {item.get('amount', 'N/A')}")

# Summary
print(f"\n{'='*65}")
print("SUMMARY")
print(f"{'='*65}")
for r in results:
    g = "PASS" if r.get("pass") else "FAIL"
    print(f"[{g}] FY{r['year']} {r['name'][:40]:<40} | {r['items']:>4} items | {r['status']}")

# Save results
import os
os.makedirs("test-results/dynamic", exist_ok=True)
with open("test-results/dynamic/new_doc_ids.json", "w") as f:
    json.dump({"new_doc_ids": new_doc_ids, "results": [{k:v for k,v in r.items() if k != "items_data"} for r in results]}, f, indent=2)
print(f"\nSaved to test-results/dynamic/new_doc_ids.json")
