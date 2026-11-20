import json
import os
import subprocess
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ["LLM_ENABLED"] = "0"

server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
    stdout=open("uvicorn_out.log", "w", encoding="utf-8"),
    stderr=subprocess.STDOUT,
    text=True,
)
print("server pid", server.pid, flush=True)

try:
    for _ in range(40):
        try:
            r = requests.get("http://127.0.0.1:8000/health", timeout=3)
            if r.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(1)
    else:
        raise SystemExit("server never became healthy")

    print("1) /health ->", requests.get("http://127.0.0.1:8000/health", timeout=10).text)

    r = requests.get("http://127.0.0.1:8000/projects", params={"city": "Riyadh"}, timeout=10).json()
    print("2) /projects?city=Riyadh -> count", r["count"])
    for x in r["results"][:3]:
        print("   ", x.get("_source"), "|", x.get("name") or x.get("title"), "|", x.get("city"))

    c = requests.post("http://127.0.0.1:8000/chat", json={"question": "Riyadh me villa"}, timeout=30).json()
    print("3) /chat mode:", c["mode"], "| reason:", c.get("reason"))
    print("   answer (first 300):", c["answer"][:300].replace("\n", " / "))
    print("   sources:", json.dumps(c["sources"], ensure_ascii=False))
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
    print("server stopped")
