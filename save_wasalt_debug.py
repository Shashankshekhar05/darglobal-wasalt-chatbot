import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

out = Path(__file__).resolve().parent / "wasalt_debug.html"
url = "https://wasalt.sa/en/property/sale/apartment-675-sqm-with-3-bedrooms-5879365"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    html = page.content()
    out.write_text(html, encoding="utf-8")
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    prop = [l for l in links if "/property/" in l]
    print("saved", out, "bytes", out.stat().st_size)
    print("total links", len(links), "property links", len(set(prop)))
    browser.close()
