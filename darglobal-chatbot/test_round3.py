import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

for _ in range(90):
    try:
        if requests.get(BASE + "/health", timeout=3).status_code == 200:
            break
    except requests.RequestException:
        time.sleep(1)

TESTS = [
    {
        "q": "Wasalt pe Riyadh me rent pe villa dikhao",
        "domain": "wasalt.sa",
        "label": "Wasalt",
    },
    {
        "q": "DarGlobal ke Dubai projects dikhao",
        "domain": "darglobal.co.uk",
        "label": "DarGlobal",
    },
    {
        "q": "شقق للبيع في الرياض",
        "domain": "wasalt.sa",
        "label": "Wasalt",
        "expect_english": True,
    },
    {
        "q": "Mujhe bada ghar chahiye Riyadh me",
        "domain": None,
        "expect_english": True,
        "villaish": True,
    },
]


def has_non_english_script(text: str) -> bool:
    for ch in text:
        o = ord(ch)
        if 0x0600 <= o <= 0x06FF or 0x0900 <= o <= 0x097F or 0x0620 <= o <= 0x064A:
            return True
    return False


results = []
for t in TESTS:
    r = requests.post(BASE + "/chat", json={"question": t["q"]}, timeout=180)
    c = r.json()
    ans = c.get("answer", "")
    sources = c.get("sources", [])
    errs = []

    if c.get("mode") != "llm":
        errs.append(f"mode={c.get('mode')}")
    if not ans.startswith("Here are the top"):
        errs.append("no header")
    if "📍" not in ans or "🔗" not in ans:
        errs.append("missing emoji markers")
    if ans.count("🔗") < 5:
        errs.append(f"only {ans.count(chr(128279))} links")
    if t.get("domain"):
        bad = [s for s in sources if t["domain"] not in s]
        if bad or not sources:
            errs.append(f"wrong sources: {bad[:2]} / n={len(sources)}")
    if t.get("expect_english") and has_non_english_script(ans):
        errs.append("non-English script in answer")
    if t.get("villaish"):
        villa_types = sum(
            1 for line in ans.splitlines()
            if "🏠" in line and any(v in line for v in ("Villa", "Rest House", "House"))
        )
        if villa_types < 3:
            errs.append(f"only {villa_types} villa/house results")

    ok = not errs
    results.append(ok)
    print("=" * 70)
    print(("PASS" if ok else "FAIL"), "|", t["q"], "|", "; ".join(errs) if errs else "all checks ok")
    print("mode:", c.get("mode"), "| sources:", len(sources))
    print(ans)
    time.sleep(1)

print("=" * 70)
print(f"RESULT: {sum(results)}/{len(results)} passed")
