import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent
FILES = [BASE / "data" / "darglobal_projects.json", BASE / "data" / "wasalt_listings.json"]
NA = "Not available"


def to_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value.replace(",", "").strip()))
        except ValueError:
            return None
    return None


def clean_file(path: Path) -> dict:
    records = json.loads(path.read_text(encoding="utf-8"))
    total = len(records)

    seen = set()
    deduped = []
    dupes = 0
    for r in records:
        url = r.get("source_url")
        if not url:
            continue
        if url in seen:
            dupes += 1
            continue
        seen.add(url)
        deduped.append(r)

    price_fixed = 0
    price_dropped = 0
    is_wasalt = "wasalt" in path.name
    for r in deduped:
        if is_wasalt and "price_sar" in r:
            n = to_number(r["price_sar"])
            if n is None:
                r["price_sar"] = NA
                price_dropped += 1
            elif n != r["price_sar"]:
                r["price_sar"] = n
                price_fixed += 1

    missing_src = sum(1 for r in deduped if not r.get("source_url"))

    changed = dupes or price_fixed or price_dropped
    if changed:
        path.write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "file": path.name,
        "total": total,
        "after_dedupe": len(deduped),
        "dupes_removed": dupes,
        "price_fixed": price_fixed,
        "price_set_na": price_dropped,
        "missing_source_url": missing_src,
        "written": bool(changed),
    }


def main() -> None:
    grand = 0
    for f in FILES:
        if not f.exists():
            print(f"MISSING: {f}")
            continue
        report = clean_file(f)
        grand += report["after_dedupe"]
        print(json.dumps(report, ensure_ascii=False))
    print(f"TOTAL RECORDS: {grand}")


if __name__ == "__main__":
    main()
