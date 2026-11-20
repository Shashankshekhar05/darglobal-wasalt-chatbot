import os
import re
import sys

import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
ROOT = r"C:\Users\shashank shekhar\OneDrive\Desktop\DarGlobal AI assistant\darglobal-chatbot"
Q1 = "What is DG1?"
Q2 = "I want a big house in Riyadh for my family"
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

    # ---------------- TEST 1: DG1 ----------------
    page.fill("#questionInput", Q1)
    page.click("#sendBtn")
    page.wait_for_timeout(9000)
    t1 = page.locator(".msg").last.inner_text()
    r1 = numbered(t1)
    print("--- ANSWER 1 ---", flush=True)
    print(t1, flush=True)
    print("--- END 1 ---", flush=True)

    check("DG1 ka jawab aaya", "DG1" in t1)
    check("'Not available' nahi bola", "Not available in scraped data" not in t1)
    check("Similar properties nahi dikhe", "similar properties" not in t1.lower())
    check("Sirf 1 result", len(r1) == 1, f"count={len(r1)}")
    check("Header DarGlobal", "DarGlobal" in t1.splitlines()[0], t1.splitlines()[0])
    check("Header '1 result'", "1 result" in t1.splitlines()[0])
    check("Wasalt ka 1 bhi nahi", "wasalt" not in t1.lower())
    check("Source darglobal.co.uk", "darglobal.co.uk" in t1.lower())
    links = page.locator(".msg").last.locator(".sources a").all_inner_texts()
    check("Source link darglobal", all("darglobal" in l.lower() for l in links) and len(links) >= 1,
          str(links))

    page.screenshot(path=os.path.join(ROOT, "fix_dg1.png"), full_page=False)
    print("saved fix_dg1.png", flush=True)

    # ---------------- TEST 2: big house ----------------
    page.fill("#questionInput", Q2)
    page.click("#sendBtn")
    page.wait_for_timeout(9000)
    t2 = page.locator(".msg").last.inner_text()
    r2 = numbered(t2)
    print("--- ANSWER 2 ---", flush=True)
    print(t2, flush=True)
    print("--- END 2 ---", flush=True)

    top3 = r2[:3]
    check("Top 3 results hain", len(top3) == 3, f"count={len(r2)}")
    check("Top 3 sab Villa", all("Villa" in x for x in top3), str(top3))
    check("Room nahi aaya", "Room" not in t2 and "Type: Room" not in t2)
    check("Rest House nahi aaya", "Rest House" not in t2)
    check("Apartment nahi aaya", "Apartment" not in t2)
    check("Riyadh hai", "Riyadh" in t2)

    page.screenshot(path=os.path.join(ROOT, "fix_big_house.png"), full_page=False)
    print("saved fix_big_house.png", flush=True)
    browser.close()

print("=" * 60)
passed = sum(1 for _, ok in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
