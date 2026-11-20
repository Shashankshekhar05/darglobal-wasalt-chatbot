import time
from pathlib import Path

from playwright.sync_api import sync_playwright

TEST_URLS = [
    "https://darglobal.co.uk/trump-tower-jeddah",
    "https://darglobal.co.uk/w-residences",
    "https://darglobal.co.uk/aida-trump-villas",
]

OUT_DIR = Path(__file__).resolve().parent / "pilot_html"
OUT_DIR.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n=== Pilot {i}/3: {url} ===")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(4000)
            html = page.content()
            out = OUT_DIR / f"pilot_{i}.html"
            out.write_text(html, encoding="utf-8")
            blocked = (
                "Incapsula" in html
                or "_Incapsula" in html
                or len(html) < 5000
            )
            print(f"LEN={len(html)} BLOCKED={blocked} saved={out.name}")
            if blocked:
                print("INCAPSULA_OR_EMPTY -> STOP")
                break
            print("OK -> continue")
        except Exception as e:
            print(f"ERROR: {e}")
            break

    browser.close()

print("\nPILOT DONE")
