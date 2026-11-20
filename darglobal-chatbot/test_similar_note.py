import os
import re
import sys

import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
ROOT = r"C:\Users\shashank shekhar\OneDrive\Desktop\DarGlobal AI assistant\darglobal-chatbot"
Q1 = "What is Price of Apartment 60 SQM with 1 Bedroom"
NOTE = (
    "Here are 2 similar listings from Wasalt — same size and price, "
    "different listings. Click Source to see each one."
)
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

    page.fill("#questionInput", Q1)
    page.click("#sendBtn")
    page.wait_for_timeout(9000)

    last = page.locator(".msg").last
    text = last.inner_text()
    rows = numbered(text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    print("--- ANSWER ---", flush=True)
    print(text, flush=True)
    print("--- END ---", flush=True)

    check("Similar listings line aa gayi", NOTE in text)
    check("Line upar hai (result 1 se pehle)",
          NOTE in text and text.index(NOTE) < text.index("1. Apartment"))
    check("Header bhi sahi hai",
          "exact match for 60 SQM, 1 Bedroom" in text)
    check("2 listings dikhi (koi chhupi nahi)", len(rows) == 2, f"count={len(rows)}")
    check("Dono alag Source URL", text.count("5893163") >= 1 and text.count("5896830") >= 1)
    check("2 clickable source links", last.locator(".sources a").count() == 2,
          f"n={last.locator('.sources a').count()}")
    check("Koi merge / group nahi",
          not re.search(r"merged|grouped|consolidat|View original", text, re.I))
    check("Listing ID field nahi dikhaya",
          not re.search(r"listing\s*id|^\s*ID\s*:", text, re.I | re.M))
    check("Sirf 60 SQM", all("60 SQM" in r for r in rows), str(rows))
    check("50/70 nahi aaya", "50 SQM" not in text and "70 SQM" not in text)
    check("Emoji nahi", not [c for c in text if ord(c) > 0x2190 and not (0x2000 <= ord(c) <= 0x206F)])

    page.screenshot(path=os.path.join(ROOT, "ui_similar_note.png"), full_page=False)
    print("saved ui_similar_note.png", flush=True)
    browser.close()

print("=" * 60)
passed = sum(1 for _, ok in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
