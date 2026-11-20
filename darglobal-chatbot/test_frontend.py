import os
import subprocess
import sys
import time

import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ["LLM_ENABLED"] = "0"
BASE = "http://127.0.0.1:8000"

server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
    stdout=open("uvicorn_fe.log", "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
    text=True,
)
print("server pid", server.pid, flush=True)
results = []


def check(name, ok, extra=""):
    results.append((name, ok))
    print(("PASS" if ok else "FAIL"), "|", name, extra)


try:
    for _ in range(40):
        try:
            if requests.get(BASE + "/health", timeout=3).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(BASE + "/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2500)

        check("Page khul raha hai", page.title() != "", f"title={page.title()!r}")
        check("Status online dikhta hai", page.locator("#statusText").inner_text() == "online")
        check("Chat window hai", page.locator("#messages").count() == 1)
        check("Filter buttons hain", page.locator(".chip").count() == 7, "7 chips expected")

        page.click('.fgroup[data-group="city"] .chip[data-value="Riyadh"]')
        page.wait_for_timeout(1500)
        count_txt = page.locator("#browseCount").inner_text()
        cards = page.locator(".card").count()
        check("City filter (Riyadh) kaam karta hai", cards > 0, f"| {count_txt} cards={cards}")
        cities = page.eval_on_selector_all(".card .tag", "els => els.map(e => e.textContent)")
        non_riyadh = [c for c in cities if c in ("Jeddah", "Dubai", "Khobar", "Makkah Al Mukarramah")]
        check("Sirf Riyadh cards dikhte hai", len(non_riyadh) == 0)

        page.click('.fgroup[data-group="listing"] .chip[data-value="rent"]')
        page.wait_for_timeout(800)
        cards2 = page.locator(".card").count()
        check("Rent filter kaam karta hai", cards2 > 0 and cards2 <= cards, f"rent cards={cards2} (was {cards})")

        page.click('.fgroup[data-group="ptype"] .chip[data-value="Apartment"]')
        page.wait_for_timeout(800)
        cards3 = page.locator(".card").count()
        titles = page.eval_on_selector_all(".card .title", "els => els.map(e => e.textContent.toLowerCase())")
        non_apt = [t for t in titles if "apartment" not in t]
        check("Apartment filter kaam karta hai", cards3 > 0 and not non_apt, f"apt cards={cards3} bad={non_apt[:3]}")

        page.fill("#questionInput", "Riyadh me villa dikhao")
        page.click("#sendBtn")
        page.wait_for_timeout(4000)
        msgs = page.locator(".msg")
        last = msgs.last
        is_bot = "msg bot" in (last.get_attribute("class") or "")
        has_sources = last.locator(".sources a").count() > 0
        srcs = last.locator(".sources a").all_inner_texts()
        check("Chat se jawab aa raha hai", is_bot, f"mode class={last.get_attribute('class')}")
        check("Sources dikh rahe hai", has_sources, f"n={len(srcs)} first={srcs[0][:60] if srcs else ''}")

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(800)
        vis_input = page.locator("#questionInput").is_visible()
        vis_send = page.locator("#sendBtn").is_visible()
        vis_filters = page.locator("#filters").is_visible()
        vis_msgs = page.locator("#messages").is_visible()
        check("Mobile pe sahi dikh raha hai", vis_input and vis_send and vis_filters and vis_msgs,
              f"input={vis_input} send={vis_send} filters={vis_filters} msgs={vis_msgs}")

        page.screenshot(path="frontend_mobile.png", full_page=False)
        page.set_viewport_size({"width": 1280, "height": 800})
        page.wait_for_timeout(300)
        page.screenshot(path="frontend_desktop.png", full_page=False)
        browser.close()
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()

print("=" * 60)
passed = sum(1 for _, ok in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
