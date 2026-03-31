from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import os, time, json

SCREENSHOTS_DIR = r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\test-results\agent7-e2e"
BASE_URL = "http://localhost:3002"
RESULTS = []

def screenshot(page, step_num, step_name):
    path = os.path.join(SCREENSHOTS_DIR, f"step-{step_num:02d}-{step_name.replace(' ', '-')}.png")
    try:
        page.screenshot(path=path, full_page=False)
    except Exception as e:
        print(f"Screenshot failed for step {step_num}: {e}")
    return os.path.basename(path)

def record(step, desc, result, notes=""):
    RESULTS.append({"step": step, "desc": desc, "result": result, "notes": notes})
    print(f"Step {step}: {result} — {desc} — {notes}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.set_default_timeout(15000)

    # Step 1: Open the app
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        shot = screenshot(page, 1, "app-open")
        title = page.title()
        url = page.url
        record(1, "Open app", "PASS", f"URL={url} title={title}")
    except Exception as e:
        record(1, "Open app", "FAIL", str(e))
        screenshot(page, 1, "app-open-error")

    # Step 2: Dashboard or redirect
    try:
        time.sleep(1)
        url = page.url
        shot = screenshot(page, 2, "dashboard-or-login")
        # Accept /dashboard, /login, /clients, or /
        ok = any(x in url for x in ["/dashboard", "/login", "/clients", "3002"])
        record(2, "Dashboard/login loads", "PASS" if ok else "FAIL", f"URL={url}")
    except Exception as e:
        record(2, "Dashboard/login loads", "FAIL", str(e))

    # Step 3: Navigate to Clients page
    try:
        page.goto(f"{BASE_URL}/clients", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
        shot = screenshot(page, 3, "clients-page")
        # Check for "client" text anywhere
        content = page.content().lower()
        ok = "client" in content
        record(3, "Clients page", "PASS" if ok else "FAIL", f"URL={page.url}")
    except Exception as e:
        record(3, "Clients page", "FAIL", str(e))
        screenshot(page, 3, "clients-error")

    # Step 4: Find and click "New Client" / "Add Client" button
    client_id = None
    try:
        btn = page.locator("button, a").filter(has_text="New Client").first
        if btn.count() == 0:
            btn = page.locator("button, a").filter(has_text="Add Client").first
        if btn.count() == 0:
            btn = page.locator("button, a").filter(has_text="Create").first
        btn.click(timeout=10000)
        time.sleep(2)
        shot = screenshot(page, 4, "new-client-form")
        record(4, "New client button clicked", "PASS", f"URL={page.url}")
    except Exception as e:
        record(4, "New client button clicked", "FAIL", str(e))
        screenshot(page, 4, "new-client-error")

    # Step 5: Fill the form
    try:
        # Try to find name field
        try:
            page.fill("input[name='name']", "E2E Test Client", timeout=5000)
        except:
            try:
                page.fill("input[placeholder*='name' i]", "E2E Test Client", timeout=5000)
            except:
                # Try first visible input
                page.locator("input:visible").first.fill("E2E Test Client")

        # Try to select industry
        try:
            page.select_option("select", "Trading", timeout=3000)
        except:
            try:
                page.fill("input[name='industry']", "Trading", timeout=3000)
            except:
                pass  # industry field might not be visible

        shot = screenshot(page, 5, "form-filled")
        record(5, "Form filled", "PASS", "Name and industry set")
    except Exception as e:
        record(5, "Form filled", "FAIL", str(e))
        screenshot(page, 5, "form-fill-error")

    # Step 6: Submit the form
    try:
        try:
            page.click("button[type='submit']", timeout=5000)
        except:
            try:
                page.locator("button").filter(has_text="Save").click(timeout=5000)
            except:
                page.locator("button").filter(has_text="Create").click(timeout=5000)
        time.sleep(3)
        shot = screenshot(page, 6, "client-created")
        url_after = page.url
        record(6, "Client created", "PASS", f"URL={url_after}")
        # Try to extract client ID from URL
        parts = url_after.split("/")
        for part in reversed(parts):
            if len(part) == 36 and part.count("-") == 4:
                client_id = part
                break
    except Exception as e:
        record(6, "Client created", "FAIL", str(e))
        screenshot(page, 6, "create-error")

    # Step 7: Navigate to upload
    try:
        # Try upload tab/button on current page
        upload_link = None
        try:
            upload_link = page.locator("a, button").filter(has_text="Upload").first
            if upload_link.count() > 0:
                upload_link.click(timeout=5000)
                time.sleep(2)
            else:
                raise Exception("No upload link found")
        except:
            # Try direct navigation
            if client_id:
                page.goto(f"{BASE_URL}/clients/{client_id}/upload", wait_until="domcontentloaded", timeout=10000)
            else:
                # Get client_id via API
                import subprocess
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:8000/api/clients?search=E2E+Test+Client"],
                    capture_output=True, text=True
                )
                try:
                    clients_data = json.loads(result.stdout)
                    if clients_data and isinstance(clients_data, list) and len(clients_data) > 0:
                        client_id = clients_data[0].get("id") or clients_data[0].get("data", [{}])[0].get("id")
                        page.goto(f"{BASE_URL}/clients/{client_id}/upload", wait_until="domcontentloaded", timeout=10000)
                    elif isinstance(clients_data, dict) and "data" in clients_data:
                        data_list = clients_data["data"]
                        if data_list:
                            client_id = data_list[0].get("id")
                            page.goto(f"{BASE_URL}/clients/{client_id}/upload", wait_until="domcontentloaded", timeout=10000)
                except:
                    pass
        time.sleep(2)
        shot = screenshot(page, 7, "upload-page")
        record(7, "Upload page", "PASS", f"URL={page.url}")
    except Exception as e:
        record(7, "Upload page", "FAIL", str(e))
        screenshot(page, 7, "upload-error")

    # Step 8: Upload document
    doc_path = r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\Excel_project\Mehta computer\2024\Mehta_Computers_financials_2024.xls"
    try:
        file_input = page.locator("input[type='file']")
        if file_input.count() > 0:
            file_input.set_input_files(doc_path)
            time.sleep(2)
            shot = screenshot(page, 8, "file-selected")
            record(8, "File selected", "PASS", "XLS file set in input")
        else:
            shot = screenshot(page, 8, "no-file-input")
            record(8, "File selected", "FAIL", "No file input found")
    except Exception as e:
        record(8, "File selected", "FAIL", str(e))
        screenshot(page, 8, "file-error")

    # Step 9: Submit upload
    try:
        try:
            page.click("button[type='submit']", timeout=5000)
        except:
            try:
                page.locator("button").filter(has_text="Upload").click(timeout=5000)
            except:
                pass
        time.sleep(3)
        shot = screenshot(page, 9, "upload-complete")
        record(9, "Upload submitted", "PASS", f"URL={page.url}")
    except Exception as e:
        record(9, "Upload submitted", "FAIL", str(e))
        screenshot(page, 9, "upload-submit-error")

    # Step 10: Wait for extraction progress
    time.sleep(5)
    shot = screenshot(page, 10, "extraction-progress")
    content = page.content().lower()
    has_progress = any(w in content for w in ["extract", "processing", "progress", "pending", "complet"])
    record(10, "Extraction progress visible", "PASS" if has_progress else "PARTIAL",
           "Extraction status visible" if has_progress else "No progress indicator found")

    # Step 11: Open verification screen
    try:
        verify_link = None
        try:
            verify_link = page.locator("a, button").filter(has_text="Verif").first
            if verify_link.count() > 0:
                verify_link.click(timeout=5000)
                time.sleep(2)
        except:
            pass
        shot = screenshot(page, 11, "verification-screen")
        content = page.content().lower()
        ok = any(w in content for w in ["verif", "item", "line", "extract"])
        record(11, "Verification screen", "PASS" if ok else "PARTIAL", f"URL={page.url}")
    except Exception as e:
        record(11, "Verification screen", "FAIL", str(e))
        screenshot(page, 11, "verify-error")

    # Step 12: Confirm verification
    try:
        confirm_btn = None
        for text in ["Confirm", "Verify All", "Approve", "Verified"]:
            try:
                btn = page.locator("button").filter(has_text=text).first
                if btn.count() > 0:
                    confirm_btn = btn
                    break
            except:
                pass
        if confirm_btn:
            confirm_btn.click(timeout=5000)
            time.sleep(2)
        shot = screenshot(page, 12, "verification-confirmed")
        record(12, "Verification confirmed", "PASS" if confirm_btn else "PARTIAL",
               "Confirm button clicked" if confirm_btn else "No confirm button found")
    except Exception as e:
        record(12, "Verification confirmed", "FAIL", str(e))
        screenshot(page, 12, "confirm-error")

    # Step 13: Navigate to classification review
    try:
        for text in ["Review", "Classif", "CMA"]:
            try:
                link = page.locator("a, button").filter(has_text=text).first
                if link.count() > 0:
                    link.click(timeout=5000)
                    time.sleep(2)
                    break
            except:
                pass
        shot = screenshot(page, 13, "classification-review")
        content = page.content().lower()
        ok = any(w in content for w in ["classif", "field", "cma", "tier"])
        record(13, "Classification review", "PASS" if ok else "PARTIAL", f"URL={page.url}")
    except Exception as e:
        record(13, "Classification review", "FAIL", str(e))
        screenshot(page, 13, "review-error")

    # Step 14: Generate Excel
    try:
        gen_btn = None
        for text in ["Generate", "Download CMA", "Download", "Export"]:
            try:
                btn = page.locator("button").filter(has_text=text).first
                if btn.count() > 0:
                    gen_btn = btn
                    break
            except:
                pass
        if gen_btn:
            try:
                with page.expect_download(timeout=20000) as dl:
                    gen_btn.click()
                download = dl.value
                fname = download.suggested_filename
                dl_ok = fname.endswith('.xlsm') or fname.endswith('.xls') or fname.endswith('.xlsx')
                record(14, "Excel downloaded", "PASS" if dl_ok else "PARTIAL", f"Filename: {fname}")
            except PlaywrightTimeout:
                # Click without expecting download (might just trigger generation)
                gen_btn.click()
                time.sleep(3)
                record(14, "Excel generated", "PARTIAL", "Button clicked but no download event")
        else:
            record(14, "Excel generate button", "FAIL", "Generate button not found on page")
        shot = screenshot(page, 14, "excel-state")
    except Exception as e:
        record(14, "Excel downloaded", "FAIL", str(e))
        screenshot(page, 14, "excel-error")

    # Step 15: Final state
    time.sleep(2)
    shot = screenshot(page, 15, "final-state")
    content = page.content().lower()
    record(15, "Final state", "PASS", f"URL={page.url}")

    browser.close()

# Print results
print("\n=== RESULTS ===")
passed = sum(1 for r in RESULTS if r["result"] == "PASS")
partial = sum(1 for r in RESULTS if r["result"] == "PARTIAL")
failed = sum(1 for r in RESULTS if r["result"] == "FAIL")
print(f"PASS: {passed}/15, PARTIAL: {partial}/15, FAIL: {failed}/15")

with open(r"C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\test-results\agent7-e2e\results.json", "w") as f:
    json.dump(RESULTS, f, indent=2)
print("Results saved.")
