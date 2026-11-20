import gzip
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent
SITEMAP = BASE / "product_sitemap.xml"
OUT = BASE / "data" / "wasalt_listings.json"
HEADERS = {"User-Agent": "DarGlobal-Assignment-Research"}
DELAY = 1.0
TARGET_SALE = 80
TARGET_RENT = 75
NA = "Not available"

SITEMAP_URLS = [
    "https://cdn.wasalt.sa/sitemap/product_sitemap_en_sa.xml.gz",
    "https://cdn.wasalt.sa/sitemap/rental_pdp_sitemap_en_sa.xml.gz",
]


def load_sitemap_urls() -> list:
    if not SITEMAP.exists():
        urls = []
        for u in SITEMAP_URLS:
            r = requests.get(u, headers=HEADERS, timeout=90)
            r.raise_for_status()
            text = gzip.decompress(r.content).decode("utf-8")
            urls += re.findall(r"<loc>(.*?)</loc>", text)
            time.sleep(1)
        SITEMAP.write_text("\n".join(urls), encoding="utf-8")
    else:
        text = SITEMAP.read_text(encoding="utf-8")
        urls = re.findall(r"<loc>(.*?)</loc>", text)
    return urls


def sample(urls: list, listing_type: str, n: int) -> list:
    hits = [u for u in urls if f"/{listing_type}/" in u]
    if not hits:
        return []
    stride = max(1, len(hits) // n)
    return hits[::stride][:n]


def fetch_listing(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=40)
    if r.status_code != 200:
        raise ValueError(f"HTTP {r.status_code}")
    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m:
        raise ValueError("no __NEXT_DATA__")
    data = json.loads(m.group(1))
    p = data.get("props", {}).get("pageProps", {}).get("propertyDetailsV3")
    if isinstance(p, list):
        p = p[0]
    if not p:
        raise ValueError("no propertyDetailsV3")
    pi = p.get("propertyInfo") or {}

    bedrooms = NA
    for a in p.get("attributes") or []:
        if a.get("key") == "noOfBedrooms":
            bedrooms = a.get("value", NA)
            break

    price = pi.get("conversionPrice") or pi.get("salePrice") or pi.get("expectedRent")
    if price in ("", None):
        price = NA
    elif not isinstance(price, (int, float)):
        try:
            price = int(float(str(price).replace(",", "")))
        except ValueError:
            price = NA

    return {
        "title": pi.get("title") or NA,
        "city": pi.get("city") or NA,
        "price_sar": price,
        "bedrooms": bedrooms,
        "type": pi.get("propertySubType") or NA,
        "listing_type": pi.get("propertyFor") or ("rent" if "/rent/" in url else "sale"),
        "source_url": url,
        "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def save(records: list) -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    urls = load_sitemap_urls()
    print(f"sitemap urls: {len(urls)}")

    todo = sample(urls, "sale", TARGET_SALE) + sample(urls, "rent", TARGET_RENT)
    print(f"to scrape: {len(todo)}")

    records = []
    failures = 0
    for i, url in enumerate(todo, 1):
        try:
            records.append(fetch_listing(url))
            status = f"OK [{records[-1]['listing_type']}] {records[-1]['city']} {records[-1]['price_sar']}"
        except Exception as e:
            failures += 1
            status = f"FAIL {e}"
        print(f"[{i}/{len(todo)}] {status}  {url}", flush=True)
        if i % 10 == 0:
            save(records)
        time.sleep(DELAY)
        if len(records) >= TARGET_SALE + TARGET_RENT:
            break

    save(records)
    na_city = sum(1 for r in records if r["city"] == NA)
    na_price = sum(1 for r in records if not isinstance(r["price_sar"], (int, float)))
    print(f"DONE saved={len(records)} failures={failures} city_NA={na_city} price_NA={na_price}")
    print(f"file: {OUT}")


if __name__ == "__main__":
    main()
