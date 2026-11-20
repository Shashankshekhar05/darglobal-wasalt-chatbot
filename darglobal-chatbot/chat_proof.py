import json
import requests

BASE = "http://localhost:8000"
questions = [
    "DarGlobal ke Dubai projects dikhao",
    "Wasalt pe Riyadh me rent pe villa dikhao",
]

results = {}
for q in questions:
    print("=" * 70)
    print("QUESTION:", q)
    print("=" * 70)
    try:
        r = requests.post(f"{BASE}/chat", json={"question": q}, timeout=180)
        data = r.json()
        results[q] = data
        print("HTTP", r.status_code)
        print("mode:", data.get("mode"))
        print("ANSWER:")
        print(data.get("answer", ""))
        print("SOURCES:")
        for s in data.get("sources", []):
            print(" ", s)
        emoji_check = [ch for ch in data.get("answer", "") if ord(ch) > 0x2190 and ord(ch) not in (0x2014, 0x2013, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026)]
        print("EMOJIS_IN_ANSWER:", emoji_check if emoji_check else "NONE")
    except Exception as e:
        print("ERROR:", e)
    print()

with open("chat_proof_output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Saved to chat_proof_output.json")