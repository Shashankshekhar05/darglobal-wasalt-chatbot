import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"

for _ in range(120):
    try:
        if requests.get(BASE + "/health", timeout=3).status_code == 200:
            break
    except requests.RequestException:
        time.sleep(1)


def has_non_english_script(text: str) -> bool:
    for ch in text:
        o = ord(ch)
        if 0x0600 <= o <= 0x06FF or 0x0900 <= o <= 0x097F:
            return True
    return False


TESTS = [
    {
        "q": "name of trump vila",
        "checks": ["trump_list"],
    },
    {
        "q": "تواصل مع الخبير",
        "checks": ["contact_reply"],
    },
    {
        "q": "شقق للبيع في الرياض",
        "checks": ["english", "format", "wasalt_only"],
    },
]


def check_trump_list(ans: str, c: dict) -> list:
    errs = []
    if c.get("mode") != "llm":
        errs.append(f"mode={c.get('mode')}")
    if ans.startswith("Not available"):
        errs.append("answer is Not available")
    low = ans.lower()
    if "trump" not in low:
        errs.append("no trump in answer")
    if "villa" not in low and "tower" not in low:
        errs.append("no villa/tower in answer")
    if ans.count("🔗") < 5:
        errs.append(f"only {ans.count(chr(128279))} links")
    return errs


def check_contact_reply(ans: str, c: dict) -> list:
    errs = []
    if c.get("mode") != "out_of_scope":
        errs.append(f"mode={c.get('mode')}")
    if "For expert contact, please visit DarGlobal / Wasalt website." not in ans:
        errs.append("missing contact reply")
    if "Not available" in ans:
        errs.append("says Not available")
    if has_non_english_script(ans):
        errs.append("non-English script")
    return errs


def check_english(ans: str, c: dict) -> list:
    errs = []
    if has_non_english_script(ans):
        errs.append("non-English script")
    return errs


def check_format(ans: str, c: dict) -> list:
    errs = []
    if c.get("mode") != "llm":
        errs.append(f"mode={c.get('mode')}")
    if not ans.startswith("Here are the top"):
        errs.append("no header")
    if "📍" not in ans or "🔗" not in ans:
        errs.append("missing emoji markers")
    if ans.count("🔗") < 5:
        errs.append(f"only {ans.count(chr(128279))} links")
    return errs


def check_wasalt_only(ans: str, c: dict) -> list:
    errs = []
    sources = c.get("sources", [])
    bad = [s for s in sources if "wasalt.sa" not in s]
    if bad or not sources:
        errs.append(f"wrong sources: {bad[:2]} / n={len(sources)}")
    return errs


CHECK_FNS = {
    "trump_list": check_trump_list,
    "contact_reply": check_contact_reply,
    "english": check_english,
    "format": check_format,
    "wasalt_only": check_wasalt_only,
}

results = []
for t in TESTS:
    r = requests.post(BASE + "/chat", json={"question": t["q"]}, timeout=300)
    c = r.json()
    ans = c.get("answer", "")
    errs = []
    for name in t["checks"]:
        errs.extend(CHECK_FNS[name](ans, c))

    ok = not errs
    results.append(ok)
    print("=" * 70)
    print(("PASS" if ok else "FAIL"), "|", t["q"], "|", "; ".join(errs) if errs else "all checks ok")
    print("mode:", c.get("mode"), "| sources:", len(c.get("sources", [])))
    print(ans)
    time.sleep(1)

print("=" * 70)
print(f"RESULT: {sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
