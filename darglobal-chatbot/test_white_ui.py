import os
import sys

import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
ROOT = r"C:\Users\shashank shekhar\OneDrive\Desktop\DarGlobal AI assistant\darglobal-chatbot"
Q = "Wasalt pe Riyadh me rent pe villa dikhao"
results = []


def check(name, ok, extra=""):
    results.append((name, ok))
    print(("PASS" if ok else "FAIL"), "|", name, extra, flush=True)


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
    page.wait_for_timeout(1200)

    html = page.content()
    check("White background", page.eval_on_selector("body", "e => getComputedStyle(e).backgroundColor") == "rgb(255, 255, 255)")
    check("No .filters panel", ".filters" not in html)
    check("No FILTERED LISTINGS", "FILTERED LISTINGS" not in html)
    check("No chips", page.locator(".chip").count() == 0)
    check("No aside", "<aside" not in html)
    check("Header brand", "Wasalt" in page.locator(".brand").inner_text())
    check("Status online", page.locator("#statusText").inner_text() == "online")
    check("Green dot", "rgb(52, 168, 83)" in page.eval_on_selector("#statusDot", "e => getComputedStyle(e).backgroundColor"))
    check("Header DarGlobal blue", "rgb(26, 115, 232)" in page.eval_on_selector(".brand .dg", "e => getComputedStyle(e).color"))
    check("Header Wasalt gold", page.eval_on_selector(".brand .wa", "e => getComputedStyle(e).color") != "rgb(26, 115, 232)")

    box = page.eval_on_selector(".shell", "e => e.getBoundingClientRect().width")
    left = page.eval_on_selector(".shell", "e => e.getBoundingClientRect().left")
    check("Chat centered max 800px", 700 <= box <= 801, f"width={box} left={left}")

    composer_r = page.eval_on_selector(".composer", "e => getComputedStyle(e).borderRadius")
    check("Google-style pill input", "999" in composer_r, composer_r)

    page.fill("#questionInput", Q)
    page.click("#sendBtn")
    page.wait_for_timeout(7000)

    last = page.locator(".msg").last
    is_bot = "msg bot" in (last.get_attribute("class") or "")
    text = last.inner_text()
    check("Bot jawab aaya", is_bot and len(text) > 40, f"len={len(text)}")
    check("No mode badge", last.locator(".badge").count() == 0)
    emoji = [c for c in text if ord(c) > 0x2190 and not (0x2000 <= ord(c) <= 0x206F)]
    check("No emoji in answer", not emoji, f"found={emoji[:5]}")

    villa = text.count("Type: Villa")
    rent = text.count("For Rent")
    numbered = [l for l in text.splitlines() if l.strip()[:2] in ("1.", "2.", "3.", "4.", "5.")]
    check("3 Villa results", villa >= 3, f"villa_type={villa} numbered={len(numbered)}")
    check("Rent tag", rent >= 3, f"For Rent={rent}")
    check("Riyadh in answer", "Riyadh" in text)
    n_src = last.locator(".sources a").count()
    check("Source links present", n_src > 0, f"n={n_src}")
    if n_src:
        style = last.locator(".sources a").first.evaluate(
            "e => getComputedStyle(e).color + ' | ' + getComputedStyle(e).textDecorationLine")
        check("Source blue + underline", "rgb(26, 115, 232)" in style and "underline" in style, style)
    bot_bg = page.eval_on_selector(".msg.bot", "e => getComputedStyle(e).backgroundColor")
    check("Bot bubble white", bot_bg == "rgb(255, 255, 255)", bot_bg)
    ubg = page.eval_on_selector(".msg.user", "e => getComputedStyle(e).backgroundColor")
    check("User bubble light blue", ubg == "rgb(232, 240, 254)", ubg)
    utxt = page.eval_on_selector(".msg.user", "e => getComputedStyle(e).color")
    check("User text dark blue", utxt == "rgb(23, 78, 166)", utxt)

    print("ANSWER_START")
    print(text)
    print("ANSWER_END", flush=True)

    page.screenshot(path=os.path.join(ROOT, "ui_white_desktop.png"), full_page=False)
    print("saved ui_white_desktop.png", flush=True)

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(900)
    mbg = page.eval_on_selector("body", "e => getComputedStyle(e).backgroundColor")
    mshell = page.eval_on_selector(".shell", "e => e.getBoundingClientRect().width")
    ib = page.locator("#questionInput").bounding_box()
    check("Mobile white bg", mbg == "rgb(255, 255, 255)", mbg)
    check("Mobile full-width chat", mshell >= 380, f"shell={mshell}")
    check("Mobile input near bottom", ib is not None and ib["y"] > 400, f"y={ib['y'] if ib else None}")
    check("Mobile send visible", page.locator("#sendBtn").is_visible())
    check("Mobile no filters", page.locator(".chip").count() == 0)
    check("Mobile emoji-free", not any(ord(c) > 0x2190 and not (0x2000 <= ord(c) <= 0x206F) for c in text))

    page.screenshot(path=os.path.join(ROOT, "ui_white_mobile.png"), full_page=False)
    print("saved ui_white_mobile.png", flush=True)

    browser.close()

print("=" * 60)
passed = sum(1 for _, ok in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
