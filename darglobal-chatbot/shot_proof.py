from playwright.sync_api import sync_playwright

url = "http://localhost:8000/"
out = r"C:\Users\shashank shekhar\OneDrive\Desktop\DarGlobal AI assistant\darglobal-chatbot\frontend_nofilters_proof.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1500)

    body = page.content()
    checks = {
        ".filters": ".filters" in body,
        "FILTERED LISTINGS": "FILTERED LISTINGS" in body,
        "<aside": "<aside" in body,
        "data-group": "data-group" in body,
        "chip": "chip" in body,
        "Riyadh filter": ">Riyadh<" in body,
        "Villa filter": ">Villa<" in body,
    }
    print("DOM checks (True = PRESENT = BAD):")
    for k, v in checks.items():
        print(f"  {k}: {v}")

    page.screenshot(path=out, full_page=True)
    print(f"Screenshot saved: {out}")
    browser.close()