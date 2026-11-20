import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BASE_URL = (os.getenv("GROK_BASE_URL", "https://api.x.ai/v1") or "").rstrip("/")
MODEL = (os.getenv("GROK_MODEL", "") or "").strip()
API_KEY = (os.getenv("GROK_API_KEY", "") or "").strip()

LLM_CALLS = 0


class LLMError(Exception):
    pass


def is_configured() -> bool:
    if os.getenv("LLM_ENABLED", "1").strip().lower() in ("0", "false", "no", "off"):
        return False
    return bool(API_KEY and MODEL)


def _source_label(chunks: list) -> str:
    hosts = set()
    for c in chunks:
        url = str(c.get("source_url") or "")
        if "wasalt.sa" in url:
            hosts.add("wasalt")
        elif "darglobal.co.uk" in url:
            hosts.add("darglobal")
    if hosts == {"wasalt"}:
        return "Wasalt"
    if hosts == {"darglobal"}:
        return "DarGlobal"
    if not hosts:
        return "scraped data"
    return "Wasalt & DarGlobal"


def build_prompt(question: str, chunks: list, header: str | None = None) -> tuple:
    context_blocks = []
    for i, c in enumerate(chunks, 1):
        context_blocks.append(f"[{i}] {c['text']}")
    context = "\n\n".join(context_blocks)
    n = len(context_blocks)
    if header is None:
        header = f"Here are the top {n} results from {_source_label(chunks)}:"
    system = (
        "You are a real estate assistant for DarGlobal and Wasalt properties. "
        "Answer ONLY from CONTEXT. If the context has no relevant data, reply exactly: "
        "Not available in scraped data. "
        "Never invent prices, cities, dates or details. "
        "Always answer in English only. Never answer in Hindi, Urdu or Arabic script, "
        "even if the user asks in that language. "
        "Format EVERY answer EXACTLY like the template below, using the context items "
        f"in order, numbered from 1 to {n}:\n"
        f"{header}\n\n"
        "1. [Name]\n"
        "City: [City], [Country]\n"
        "Type: [Apartment / Villa / Tower] | Bedrooms: [Number]\n"
        "Price: [Price] SAR — [For Sale / For Rent / Status]\n"
        "Source: [source_url]\n\n"
        "Rules: copy values only from CONTEXT; if a value is missing, omit that segment "
        "(missing bedrooms -> only the Type line; missing price -> write "
        "'Price: Not available)'; "
        f"repeat the block for every one of the {n} context items; "
        "no extra commentary before or after."
)
    user = f"CONTEXT:\n{context}\n\nQUESTION: {question}"
    return system, user


def ask_grok(question: str, chunks: list, timeout: int = 90, header: str | None = None) -> dict:
    """Call Grok-compatible chat completions API. Raises LLMError on any failure."""
    global LLM_CALLS
    if not API_KEY:
        raise LLMError("GROK_API_KEY not set")
    if not MODEL:
        raise LLMError("GROK_MODEL not set")

    system, user = build_prompt(question, chunks, header=header)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    LLM_CALLS += 1
    print(f"LLM_CALL #{LLM_CALLS} model={MODEL} base={BASE_URL}", flush=True)

    try:
        r = requests.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise LLMError(f"request failed: {e}") from e

    if r.status_code != 200:
        raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")

    try:
        data = r.json()
        answer = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError) as e:
        raise LLMError(f"unexpected response shape: {e}") from e

    if not answer or not str(answer).strip():
        raise LLMError("empty answer from model")

    return {"answer": str(answer).strip()}
