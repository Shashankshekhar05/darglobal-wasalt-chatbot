import os
import re
import sys

import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
ROOT = r"C:\Users\shashank shekhar\OneDrive\Desktop\DarGlobal AI assistant\darglobal-chatbot"
Q1 = "What is Price of Apartment 60 SQM with 1 Bedroom"
Q2 = "Wasalt pe Riyadh me rent pe villa dikhao"
results = []


def check(name, ok, extra=""):
    results.append((name, ok))
    print(("PASS" if ok else "FAIL"), "|", name, extra, flush=True)


def numbered(text):
    return [l.strip() for l in text.splitlines() if re.match(r"^\d+\.\s", l.strip())]


for _ in range(20):
    try:
        if requests.get(BASE + "/health", timeout=3).status_code == 200:
            break
    except requests.RequestException:
        pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE + "/", wait_until="load", timeout=30000)
    page.wait_for_timeout(1000)

    # ---------------- TEST 1: specific / exact ----------------
    page.fill("#questionInput", Q1)
    page.click("#sendBtn")
    page.wait_for_timeout(8000)
    t1 = page.locator(".msg").last.inner_text()
    n1 = numbered(t1)
    header1 = t1.splitlines()[0].strip()

    print("--- ANSWER 1 ---", flush=True)
    print(t1, flush=True)
    print("--- END ANSWER 1 ---", flush=True)

    check("Q1: exact match header", "exact match for 60 SQM, 1 Bedroom" in header1, header1)
    check("Q1: exactly 2 results", len(n1) == 2, f"count={len(n1)}")
    check("Q1: saare 60 SQM", len(n1) == 2 and all("60 SQM" in l for l in n1), str(n1))
    check("Q1: 50 SQM nahi aaya", "50 SQM" not in t1)
    check("Q1: 70 SQM nahi aaya", "70 SQM" not in t1)
    check("Q1: 300/434 SQM nahi aaya", "300 SQM" not in t1 and "434 SQM" not in t1)
    check("Q1: 1 Bedroom sahi", t1.count("Bedrooms: 1") == 2, f"n={t1.count('Bedrooms: 1')}")
    check("Q1: 2 source links", page.locator(".msg").last.locator(".sources a").count() == 2,
          f"n={page.locator('.msg').last.locator('.sources a').count()}")
    check("Q1: 50/70 kahin nahi (pura text)",
          not re.search(r"\b(50|70|65|75)\s*SQM", t1))

    page.screenshot(path=os.path.join(ROOT, "ui_exact_60sqm.png"), full_page=False)
    print("saved ui_exact_60sqm.png", flush=True)

    # ---------------- TEST 2: broad ----------------
    page.fill("#questionInput", Q2)
    page.click("#sendBtn")
    page.wait_for_timeout(8000)
    t2 = page.locator(".msg").last.inner_text()
    n2 = numbered(t2)

    print("--- ANSWER 2 ---", flush=True)
    print(t2, flush=True)
    print("--- END ANSWER 2 ---", flush=True)

    check("Q2: broad header (exact match nahi)", "exact match" not in t2)
    check("Q2: 3 Villa results", t2.count("Type: Villa") == 3, f"villa={t2.count('Type: Villa')}")
    check("Q2: 3 For Rent", t2.count("For Rent") == 3, f"rent={t2.count('For Rent')}")
    check("Q2: 3 numbered rows", len(n2) == 3, f"count={len(n2)}")
    check("Q2: Riyadh", "Riyadh" in t2)
    check("Q2: saare villa Riyadh rent",
          all("Villa" in l for l in n2), str(n2))

    page.screenshot(path=os.path.join(ROOT, "ui_broad_villa.png"), full_page=False)
    print("saved ui_broad_villa.png", flush=True)

    browser.close()

print("=" * 60)
passed = sum(1 for _, ok in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
