import json
import os
import subprocess
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ["LLM_ENABLED"] = "1"

server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
    stdout=open("uvicorn_llm.log", "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
    text=True,
)
print("server pid", server.pid, flush=True)

QUESTIONS = [
    "Trump Tower Jeddah kya hai?",
    "Riyadh me 3 bedroom apartment dikhao",
]

try:
    for _ in range(40):
        try:
            if requests.get("http://127.0.0.1:8000/health", timeout=3).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(1)
    else:
        raise SystemExit("server never became healthy")

    for q in QUESTIONS:
        print("=" * 70)
        print("Q:", q)
        r = requests.post("http://127.0.0.1:8000/chat", json={"question": q}, timeout=180)
        c = r.json()
        print("mode:", c["mode"])
        print("answer:", c["answer"])
        print("sources:")
        for s in c.get("sources", []):
            print("  -", s)
        time.sleep(1)
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
    log = open("uvicorn_llm.log", encoding="utf-8").read()
    calls = [l for l in log.splitlines() if "LLM_CALL" in l or "LLM_FAIL" in l]
    print("=" * 70)
    print("LLM call log lines:", len(calls))
    for l in calls:
        print(" ", l)
    print("server stopped")
