import os
import re
import sys

import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8000"
ROOT = r"C:\Users\shashank shekhar\OneDrive\Desktop\DarGlobal AI assistant\darglobal-chatbot"
Q = "Show me DarGlobal projects in Dubai"
results = []


def check(name, ok, extra=""):
    results.append((name, ok))
    print(("PASS" if ok else "FAIL"), "|", name, extra, flush=True)


for _ in range(30):
    try:
        if requests.get(BASE + "/health", timeout=3).status_code == 200:
            break
    except requests.RequestException:
        pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE + "/", wait_until="load", timeout=30000)
    page.wait_for_timeout(1500)
    html = page.content()

    # ---------- layout / theme ----------
    check("White background", page.eval_on_selector("body", "e => getComputedStyle(e).backgroundColor") == "rgb(255, 255, 255)")
    w = page.eval_on_selector(".shell", "e => e.getBoundingClientRect().width")
    check("Chat centered, max 800px", 700 <= w <= 801, f"width={w}")
    check("Header me DarGlobal + Wasalt", page.locator(".brand").inner_text().replace("\n", "").strip() == "DarGlobal + Wasalt",
          repr(page.locator(".brand").inner_text()))
    check("Right me AI Assistant + Online",
          "AI Assistant" in page.locator(".status").inner_text() and "Online" in page.locator(".status").inner_text(),
          repr(page.locator(".status").inner_text()))
    check("Green online dot", page.eval_on_selector("#statusDot", "e => getComputedStyle(e).backgroundColor") == "rgb(24, 128, 56)")

    # no sidebar / watchlist / suggested / filters / pdf
    low = html.lower()
    for bad in ("sidebar", "watchlist", "suggested", "filters", "chip", "<aside", "pdf"):
        check(f"No {bad}", bad not in low)

    ph = page.get_attribute("#questionInput", "placeholder")
    check("Input placeholder", ph == "Ask me anything about DarGlobal projects or Wasalt listings...", repr(ph))
    btn_bg = page.eval_on_selector("#sendBtn", "e => getComputedStyle(e).backgroundColor")
    btn_r = page.eval_on_selector("#sendBtn", "e => getComputedStyle(e).borderRadius")
    check("Blue round Send button", btn_bg == "rgb(26, 115, 232)" and btn_r.startswith("50%"), f"{btn_bg} {btn_r}")
    check("Send me arrow icon", page.locator("#sendBtn svg").count() == 1)

    # ---------- the question ----------
    page.fill("#questionInput", Q)
    page.click("#sendBtn")
    page.wait_for_timeout(9000)

    bot = page.locator(".msg.bot").last
    cards = bot.locator(".card")
    n = cards.count()
    print("--- BOT TEXT ---", flush=True)
    print(bot.inner_text(), flush=True)
    print("--- END ---", flush=True)

    check("5 cards aaye", n == 5, f"count={n}")
    check("AI ASSISTANT label", bot.locator(".who").inner_text().strip().upper() == "AI ASSISTANT",
          repr(bot.locator(".who").inner_text()))

    hosts, prices, names = [], [], []
    for i in range(n):
        c = cards.nth(i)
        names.append(c.locator(".nm").inner_text())
        href = c.locator(".src a").get_attribute("href") or ""
        hosts.append(href)
        prices.append(c.locator(".row").nth(2).inner_text())
        check(f"card{i+1} Source original URL", href.startswith("https://darglobal.co.uk/"), href)
        check(f"card{i+1} Price: Not available", c.locator(".row").nth(2).inner_text() == "Price: Not available",
              repr(c.locator(".row").nth(2).inner_text()))
        check(f"card{i+1} Type line", c.locator(".row").nth(1).inner_text().startswith("Type:"),
              repr(c.locator(".row").nth(1).inner_text()))
        check(f"card{i+1} Source row", c.locator(".row").nth(3).inner_text().startswith("Source:"),
              repr(c.locator(".row").nth(3).inner_text()))

    check("Sab card DarGlobal", all("darglobal.co.uk" in h for h in hosts), str(hosts))
    check("Wasalt ka 1 bhi nahi", "wasalt" not in bot.inner_text().lower())
    check("Koi dummy price (SAR) nahi", "sar" not in bot.inner_text().lower())
    check("5 alag project names", len(set(names)) == 5, str(names))
    check("City line Dubai", all("Dubai" in cards.nth(i).locator(".row").first.inner_text() for i in range(n)))

    # card styles
    cbg = page.eval_on_selector(".msg.bot .card", "e => getComputedStyle(e).backgroundColor")
    check("Card white", cbg == "rgb(255, 255, 255)", cbg)
    src_style = bot.locator(".src a").first.evaluate(
        "e => getComputedStyle(e).color + ' | ' + getComputedStyle(e).textDecorationLine")
    check("Source blue + underline", "rgb(26, 115, 232)" in src_style and "underline" in src_style, src_style)

    # user bubble
    ub = page.locator(".msg.user").last
    check("User bubble light blue", page.eval_on_selector(".msg.user", "e => getComputedStyle(e).backgroundColor") == "rgb(232, 240, 254)")
    check("User right side", ub.bounding_box()["x"] > 500, f"x={ub.bounding_box()['x']}")

    page.screenshot(path=os.path.join(ROOT, "ui_mockup_dubai.png"), full_page=False)
    print("saved ui_mockup_dubai.png", flush=True)

    # ---------- mobile ----------
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(800)
    check("Mobile white", page.eval_on_selector("body", "e => getComputedStyle(e).backgroundColor") == "rgb(255, 255, 255)")
    check("Mobile chat full width", page.eval_on_selector(".shell", "e => e.getBoundingClientRect().width") >= 380)
    ib = page.locator("#questionInput").bounding_box()
    check("Mobile input neeche", ib is not None and ib["y"] > 400, f"y={ib['y'] if ib else None}")
    check("Mobile 5 cards dikhte hai", page.locator(".msg.bot").last.locator(".card").count() == 5)
    page.screenshot(path=os.path.join(ROOT, "ui_mockup_mobile.png"), full_page=False)
    print("saved ui_mockup_mobile.png", flush=True)

    browser.close()

print("=" * 60)
passed = sum(1 for _, ok in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
