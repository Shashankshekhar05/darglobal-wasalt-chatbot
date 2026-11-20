import json
import re
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from . import llm
from .retriever import (
    _doc_area_sqm,
    _source_filter,
    query_info,
    query_specs,
    query_type_filter,
    search,
    semantic_nearest,
)

NA_MSG = "Not available in scraped data"
CONTACT_MSG = "For expert contact, please visit DarGlobal / Wasalt website. Which property are you interested in?"
PERSON_MSG = "This looks like a person's name, not a property. I can help you with DarGlobal projects or Wasalt listings."
CONTACT_RE = re.compile(
    r"تواصل|الخبير|خبير|contact.{0,25}expert|expert.{0,25}contact|speak to expert|talk to expert|call expert",
    re.IGNORECASE,
)

BASE = Path(__file__).resolve().parent.parent
PROJECTS_FILE = BASE / "data" / "darglobal_projects.json"
LISTINGS_FILE = BASE / "data" / "wasalt_listings.json"
STATIC_DIR = Path(__file__).resolve().parent / "static"
NA = "Not available"

app = FastAPI(title="DarGlobal + Wasalt Chatbot")

_records_cache: dict = {}


def _load_records() -> dict:
    if not _records_cache:
        for key, path in (("projects", PROJECTS_FILE), ("listings", LISTINGS_FILE)):
            if path.exists():
                _records_cache[key] = json.loads(path.read_text(encoding="utf-8"))
            else:
                _records_cache[key] = []
    return _records_cache


class ChatRequest(BaseModel):
    question: str


def _chunk_text(r: dict) -> str:
    title = r.get("name") or r.get("title") or "Untitled"
    parts = [f"{title}"]
    for key in ("city", "country", "type", "brand", "status", "bedrooms", "listing_type", "price_sar", "description"):
        v = r.get(key)
        if v is None or v == "" or v == NA:
            continue
        parts.append(f"{key}: {v}")
    if r.get("source_url"):
        parts.append(f"source: {r['source_url']}")
    return " | ".join(parts)


def _retrieved_payload(hits: list) -> list:
    out = []
    for r in hits:
        out.append({
            "text": _chunk_text(r),
            "source_url": r.get("source_url"),
            "city": r.get("city"),
        })
    return out


def _source_label(hits: list) -> str:
    sources = {r.get("_source") for r in hits}
    if sources == {"wasalt"}:
        return "Wasalt"
    if sources == {"darglobal"}:
        return "DarGlobal"
    if not sources:
        return "scraped data"
    return "Wasalt & DarGlobal"


def _spec_label(specs: dict) -> str:
    """Human label for exact specs: '60 SQM, 1 Bedroom'."""
    parts = []
    area = specs.get("area_sqm")
    if area is not None:
        parts.append(f"{int(area)} SQM" if float(area).is_integer() else f"{area} SQM")
    beds = specs.get("bedrooms")
    if beds is not None:
        b = int(beds)
        parts.append(f"{b} Bedroom" if b == 1 else f"{b} Bedrooms")
    return ", ".join(parts)


def _similar_note(hits: list) -> str:
    """Info line when >=2 separate listings look identical.

    Listings are NEVER merged: the data has no address / building / coordinates,
    so identical attributes do not prove it is the same property.
    """
    if len(hits) < 2:
        return ""
    groups: dict = {}
    for idx, h in enumerate(hits):
        key = (
            str(h.get("title") or h.get("name") or "").strip().lower(),
            h.get("price_sar"),
            str(h.get("city") or "").strip().lower(),
            h.get("bedrooms"),
            _doc_area_sqm(h),
        )
        url = str(h.get("source_url") or "").strip() or f"#{idx}"
        groups.setdefault(key, set()).add(url)
    biggest = max((len(v) for v in groups.values()), default=0)
    if biggest < 2:
        return ""
    label = _source_label(hits)
    return (
        f"Here are {biggest} similar listings from {label} — same size and price, "
        f"different listings. Click Source to see each one."
    )


def _count_phrase(n: int, label: str) -> str:
    if n == 1:
        return f"Here is 1 result from {label}"
    return f"Here are {n} results from {label}"


def _host(url: str) -> str:
    m = re.match(r"^https?://([^/]+)", str(url or ""))
    return m.group(1) if m else str(url or "")


def _ui_fields(hits: list, question: str = "", caption: str | None = None) -> dict:
    """Extra fields the card UI needs. `answer` stays the full plain text."""
    header = _results_header(hits, question) if hits and question else ""
    note = _similar_note(hits)
    if caption is None:
        caption = "\n".join(x for x in (header, note) if x)
    return {
        "caption": caption,
        "header": header,
        "note": note,
        "results": _structured_results(hits),
    }


def _no_ui() -> dict:
    return {"caption": "", "header": "", "note": "", "results": []}

def _country_of(h: dict) -> str:
    country = h.get("country")
    if country and country != "Not available":
        return country
    city = h.get("city") or "Not available"
    if h.get("_source") == "wasalt" and city != "Not available":
        return "Saudi Arabia"
    return "Not available"


def _price_text(h: dict) -> str:
    """Price straight from scraped data. Never invented.

    No price in the record -> exactly "Not available" (no guessed figures).
    """
    price = h.get("price_sar")
    if isinstance(price, (int, float)) and not isinstance(price, bool):
        if h.get("listing_type") == "rent":
            tag = "For Rent"
        elif h.get("listing_type") == "sale":
            tag = "For Sale"
        else:
            status = h.get("status")
            tag = status if status not in (None, "", "Not available") else ""
        return f"{price:,} SAR" + (f" — {tag}" if tag else "")
    return "Not available"


def _structured_results(hits: list) -> list:
    """Card data for the UI. Only fields present in scraped records."""
    out = []
    for h in hits:
        out.append({
            "name": h.get("name") or h.get("title") or "Unnamed",
            "city": h.get("city") or "Not available",
            "country": _country_of(h),
            "type": h.get("type") or "Not available",
            "price": _price_text(h),
            "source_url": h.get("source_url") or "",
            "source_host": _host(h.get("source_url") or ""),
        })
    return out


def _results_header(hits: list, question: str, top_k: int = 5) -> str:
    """Answer header. When a Type filter limits results below top_k, say so:
    'Here are 3 results from Wasalt — only 3 villas available...'"""
    label = _source_label(hits)
    base = _count_phrase(len(hits), label)
    specs = query_specs(question)
    if specs and _spec_label(specs):
        return f"{base} — exact match for {_spec_label(specs)}"
    if len(hits) >= top_k:
        return f"Here are the top {len(hits)} results from {label}:"
    qtypes = query_type_filter(question)
    if qtypes:
        noun = qtypes[0]
        plural = noun if len(hits) == 1 else noun + "s"
        return f"{base} — only {len(hits)} {plural} available..."
    return f"{base}:"


def _with_note(answer: str, header: str, note: str) -> str:
    """Insert the similar-listings line right under the header (once only)."""
    if not note or note in answer or not header:
        return answer
    return answer.replace(header, f"{header}\n{note}", 1)


def _format_results(hits: list, header: str | None = None) -> str:
    """Deterministic answer in plain English format (no emojis, no invented data)."""
    label = _source_label(hits)
    if header is None:
        header = f"Here are the top {len(hits)} results from {label}:"
    lines = [header] if header else []
    note = _similar_note(hits)
    if note and note not in (header or ""):
        lines.append(note)
    for i, h in enumerate(hits, 1):
        name = h.get("name") or h.get("title") or "Unnamed"
        city = h.get("city") or "Not available"
        country = h.get("country")
        if not country or country == "Not available":
            country = "Saudi Arabia" if h.get("_source") == "wasalt" and city != "Not available" else "Not available"
        typ = h.get("type") or "Not available"
        bed = h.get("bedrooms")
        price = h.get("price_sar")

        lines.append(f"{i}. {name}")
        lines.append(f"City: {city}, {country}")
        bed_str = f"Bedrooms: {bed}" if bed not in (None, "", "Not available") else ""
        type_str = f"Type: {typ}"
        if bed not in (None, "", "Not available"):
            lines.append(f"   {bed_str} | {type_str}")
        else:
            lines.append(f"   {type_str}")
        if isinstance(price, (int, float)):
            if h.get("listing_type") == "rent":
                tag = "For Rent"
            elif h.get("listing_type") == "sale":
                tag = "For Sale"
            else:
                tag = h.get("status") if h.get("status") not in (None, "Not available") else ""
            tag_str = f" — {tag}" if tag else ""
            lines.append(f"   Price: {price:,} SAR{tag_str}")
        else:
            status = h.get("status") if h.get("status") not in (None, "Not available") else ""
            tag_str = f" — {status}" if status else ""
            lines.append(f"   Price: Not available{tag_str}")
        lines.append(f"   Source: {h.get('source_url')}")
    lines.append("")
    return "\n".join(lines)


def _format_ok(answer: str, hits: list, header: str) -> bool:
    """Check that an LLM answer really follows the plain English format."""
    if header not in answer:
        return False
    if answer.count("Source:") < max(1, len(hits) - 1):
        return False
    low = answer.lower()
    names = [(h.get("name") or h.get("title") or "").lower() for h in hits]
    matched = sum(1 for n in names if len(n) >= 6 and n[:20] in low)
    return matched >= max(1, len(hits) - 1)


def _fallback(question: str, hits: list, reason: str) -> dict:
    return {
        "question": question,
        "mode": "fallback",
        "reason": reason,
        "answer": _format_results(hits, header=_results_header(hits, question)),
        "sources": [h.get("source_url") for h in hits if h.get("source_url")],
        **_ui_fields(hits, question),
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/projects")
def projects(city: str = "", source: str = "") -> dict:
    data = _load_records()
    rows = [dict(r, _source="darglobal") for r in data["projects"]]
    rows += [dict(r, _source="wasalt") for r in data["listings"]]
    if city:
        rows = [r for r in rows if str(r.get("city", "")).lower() == city.lower()]
    if source:
        rows = [r for r in rows if r["_source"] == source.lower()]
    return {"count": len(rows), "city": city or None, "results": rows}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    question = (req.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is empty")

    if CONTACT_RE.search(question):
        return {
            "question": question,
            "mode": "out_of_scope",
            "answer": CONTACT_MSG,
            "sources": [],
            **_no_ui(),
        }

    hits = search(question, top_k=5)
    chunks = _retrieved_payload(hits)

    if not chunks:
        info = query_info(question)
        if info["arabic_left"] or info["unknown_ratio"] >= 0.99:
            return {
                "question": question,
                "mode": "out_of_scope",
                "answer": PERSON_MSG,
                "sources": [],
                **_no_ui(),
            }
        similar = semantic_nearest(question, n=3, source=_source_filter(question.lower()))
        if similar:
            cards = _format_results(similar, header="")
            answer = f"{NA_MSG}. Here are similar properties:\n\n{cards}"
            return {
                "question": question,
                "mode": "no_match",
                "answer": answer,
                "sources": [h.get("source_url") for h in similar if h.get("source_url")],
                **_ui_fields(
                    similar,
                    question,
                    caption=f"{NA_MSG}. Here are similar properties:",
                ),
            }
        return {
            "question": question,
            "mode": "retriever-empty",
            "answer": NA_MSG,
            "sources": [],
            **_no_ui(),
        }

    if not llm.is_configured():
        return _fallback(question, hits, "llm_disabled_or_not_configured")

    header = _results_header(hits, question)
    try:
        result = llm.ask_grok(question, chunks, header=header)
    except llm.LLMError as e:
        print(f"LLM_FAIL: {e}", flush=True)
        return _fallback(question, hits, f"llm_error: {e}")

    answer = result["answer"]
    if not _format_ok(answer, hits, header):
        answer = _format_results(hits, header=header)
    answer = _with_note(answer, header, _similar_note(hits))

    return {
        "question": question,
        "mode": "llm",
        "answer": answer,
        "sources": [h.get("source_url") for h in hits if h.get("source_url")],
        **_ui_fields(hits, question),
    }
