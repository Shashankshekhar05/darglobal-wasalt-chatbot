import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent
DATA_FILES = [BASE / "data" / "darglobal_projects.json", BASE / "data" / "wasalt_listings.json"]

STOPWORDS = {
    "me", "mein", "pe", "ka", "ke", "ki", "se", "ko", "hai", "kya", "aur", "wala", "wali",
    "dikhao", "dikha", "chahiye", "karo", "me?", "kiya", "kaun", "kaise", "kahan", "kab",
    "mujhe", "hamein", "hamen", "karke", "do", "dijiye", "mila", "milo", "name", "full",
    "please", "haal", "theek", "batao", "bataye", "ho",
    "the", "a", "an", "in", "on", "of", "for", "with", "and", "or", "to", "is", "are",
    "at", "by", "from", "up", "be", "this", "that", "my", "i", "we", "you", "it",
    "show", "find", "give", "list", "some", "any", "near", "into",
}

# Arabic -> English keyword map (query side only)
ARABIC_MAP = {
    "شقق": "Apartment",
    "شقة": "Apartment",
    "شقه": "Apartment",
    "فيلا": "Villa",
    "فيلات": "Villa",
    "للبيع": "sale",
    "بيع": "sale",
    "للإيجار": "rent",
    "للايجار": "rent",
    "ايجار": "rent",
    "إيجار": "rent",
    "الرياض": "Riyadh",
    "جدة": "Jeddah",
    "دبي": "Dubai",
    "تواصل مع الخبير": "contact expert",
}

# Hinglish/Urdu -> English keyword map (query side)
LATIN_MAP = {
    "ghar": "villa house",
    "bada": "large",
    "kothi": "villa",
    "bangla": "villa",
    "makkan": "house",
}

MIN_SEM = 0.25
MIN_COVERAGE = 0.5
RRF_K = 60
SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

PROPERTY_TYPES = {
    "apartment", "villa", "house", "plot", "penthouse", "room", "tower", "mansion",
    "land", "chalet", "floor", "hotel", "residence", "rest", "office", "shop",
    "building", "home", "flat", "property", "bedroom",
}

# Words that trigger a HARD Type filter (only unambiguous property kinds; name
# words like tower/hotel/house are excluded so project names don't over-filter).
HARD_TYPE_WORDS = {
    "villa", "apartment", "flat", "penthouse", "room", "plot", "land",
    "mansion", "chalet",
}

# Query word -> canonical doc Type value (flat listings are typed Apartment).
TYPE_SYNONYMS = {"flat": "apartment"}

# Words removed before an exact record-name match ("What is DG1?" -> "dg1").
QUESTION_WORDS = {
    "what", "which", "who", "when", "where", "why", "how", "is", "are", "was",
    "were", "do", "does", "did", "tell", "about", "please", "name", "kya",
    "hai", "hain", "kaun", "kya", "batao", "bata", "ka", "ke", "ki",
}

# Single-word record names that are too generic to treat as an entity name.
GENERIC_NAME_WORDS = {
    "project", "projects", "property", "properties", "listing", "listings",
    "home", "house", "villa", "apartment", "plot", "room", "tower", "land",
}

# Semantic phrases -> canonical property type (query side only).
# "big house" / "family house" / "large house" all mean Villa.
SEMANTIC_TYPE_PHRASES = [
    (r"\b(?:big|large|huge|spacious)\s+(?:house|home)\b", "villa"),
    (r"\bfamily\s+(?:house|home)\b", "villa"),
    (r"\bhouse\s+for\s+(?:my\s+)?family\b", "villa"),
    (r"\bfor\s+(?:my\s+)?family\b", "villa"),
]

# Exact numeric specs in a query: "60 SQM" -> area, "1 Bedroom" -> bedrooms.
AREA_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:sqm|sq\.?\s*m|square\s*m(?:eter)?s?)", re.IGNORECASE)
BED_RE = re.compile(r"(\d+)\s*bed(?:room)?s?", re.IGNORECASE)
DOC_AREA_RE = re.compile(r"(\d+(?:\.\d+)?)\s*sqm", re.IGNORECASE)


def parse_query_specs(query: str) -> dict:
    """Exact numeric constraints demanded by the query.

    {"area_sqm": 60.0, "bedrooms": 1} — empty dict means a broad query.
    """
    q = _translate(query or "")
    specs: dict = {}
    m = AREA_RE.search(q)
    if m:
        specs["area_sqm"] = float(m.group(1))
    m = BED_RE.search(q)
    if m:
        specs["bedrooms"] = int(m.group(1))
    return specs


def _doc_area_sqm(rec: dict) -> float | None:
    """Area parsed from the record title, e.g. 'Apartment 60 SQM ...' -> 60.0."""
    m = DOC_AREA_RE.search(str(rec.get("title") or rec.get("name") or ""))
    return float(m.group(1)) if m else None


def _doc_bedrooms(rec: dict) -> float | None:
    b = rec.get("bedrooms")
    if isinstance(b, bool):
        return None
    if isinstance(b, (int, float)):
        return float(b)
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(b or ""))
    return float(m.group(1)) if m else None


def _specs_match(rec: dict, specs: dict) -> bool:
    """True when the record satisfies every exact spec in the query."""
    area = specs.get("area_sqm")
    if area is not None:
        got = _doc_area_sqm(rec)
        if got is None or abs(got - area) > 1e-6:
            return False
    beds = specs.get("bedrooms")
    if beds is not None:
        got = _doc_bedrooms(rec)
        if got is None or abs(got - beds) > 1e-6:
            return False
    return True


def _clean_query_words(query: str) -> list:
    """Question words + punctuation stripped: 'What is DG1?' -> ['dg1']."""
    q = re.sub(r"[^a-z0-9\s]", " ", _norm(_translate(query or "")))
    out = []
    for w in q.split():
        if not w or w in STOPWORDS or w in QUESTION_WORDS:
            continue
        if len(w) <= 1 and not w.isdigit():
            continue
        out.append(w)
    return out


def _exact_name_hits(query: str, name_keys: list) -> list:
    """Indices of records whose name/title IS the entity being asked about.

    Used so a short query like 'What is DG1?' resolves to that one record
    instead of falling back to 'similar properties' from the other source.
    """
    words = _clean_query_words(query)
    if not words:
        return []
    phrase = " ".join(words)
    hits = []
    for i, key in enumerate(name_keys):
        if not key:
            continue
        if key == phrase:
            hits.append(i)
        elif len(key.split()) == 1 and key not in GENERIC_NAME_WORDS and key in words:
            hits.append(i)
    return hits


def _load_docs() -> list:
    docs = []
    for f in DATA_FILES:
        if not f.exists():
            continue
        source = "darglobal" if "darglobal" in f.name else "wasalt"
        for r in json.loads(f.read_text(encoding="utf-8")):
            rec = dict(r)
            rec["_source"] = source
            url = str(rec.get("source_url", "")).lower()
            if source == "wasalt" and "wasalt.sa" not in url:
                continue
            if source == "darglobal" and "darglobal.co.uk" not in url:
                continue
            docs.append(rec)
    return docs


def _doc_text(rec: dict) -> str:
    parts = []
    for k, v in rec.items():
        if k in ("scraped_at", "_source", "price_sar") or v is None:
            continue
        if isinstance(v, (int, float)):
            parts.append(f"{v}")
        else:
            s = str(v)
            if s != "Not available":
                parts.append(s)
    return " ".join(parts)


def _tokens(text: str) -> list:
    return re.findall(r"[a-z0-9]+", text.lower())


def _token_set(text: str) -> set:
    return set(_tokens(text))


def _norm(text: str) -> str:
    """Lowercase + crude singularization so bedroom/bedrooms, villa/villas match."""

    def w(m):
        word = m.group(0)
        if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    return re.sub(r"[A-Za-z]+", w, text.lower())


def _translate(query: str) -> str:
    def repl(m):
        return ARABIC_MAP.get(m.group(0), m.group(0))

    out = re.sub(r"[\u0600-\u06FF]+", repl, query)
    for word, replacement in LATIN_MAP.items():
        out = re.sub(rf"\b{word}\b", replacement, out, flags=re.IGNORECASE)
    return out


def _doc_type_matches(rec: dict, wanted: set) -> bool:
    """True if the record's Type field contains any wanted canonical type word."""
    t = str(rec.get("type") or "").lower()
    if not t or t == "not available":
        return False
    return bool(set(_tokens(_norm(t))) & wanted)


def _listing_type_filter(query: str) -> str:
    """Hard listing_type intent from query: 'rent' | 'sale' | ''.

    Matches on the translated+normalized query, so Arabic/الإيجار -> 'rent',
    للبيع -> 'sale' (via ARABIC_MAP) is covered automatically.
    """
    q = query.lower()
    rent_hit = bool(re.search(r"\brent(al)?\b", q))
    sale_hit = bool(re.search(r"\b(sale|buy|purchase)\b", q))
    if rent_hit and not sale_hit:
        return "rent"
    if sale_hit and not rent_hit:
        return "sale"
    return ""


def _source_filter(query: str) -> str:
    q = query.lower()
    has_wasalt = "wasalt" in q
    has_dg = "darglobal" in q or "dar global" in q
    if has_wasalt and not has_dg:
        return "wasalt"
    if has_dg and not has_wasalt:
        return "darglobal"
    if has_wasalt and has_dg:
        return ""
    return ""


def _lev1(a: str, b: str) -> int:
    """Levenshtein distance with early exit at 2."""
    if a == b:
        return 0
    if abs(len(a) - len(b)) > 1:
        return 2
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > 1:
            return 2
        prev = cur
    return prev[-1]


class _BM25:
    def __init__(self, token_lists: list, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.n = len(token_lists)
        self.doc_len = np.array([max(len(t), 1) for t in token_lists], dtype=float)
        self.avgdl = float(self.doc_len.mean()) or 1.0
        self.tf = [Counter(t) for t in token_lists]
        df = Counter()
        for t in token_lists:
            df.update(set(t))
        self.idf = {
            term: math.log(1 + (self.n - d + 0.5) / (d + 0.5)) for term, d in df.items()
        }

    def scores(self, qterms: list) -> np.ndarray:
        out = np.zeros(self.n)
        for term in qterms:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i in range(self.n):
                f = self.tf[i].get(term, 0)
                if f:
                    out[i] += idf * (f * (self.k1 + 1)) / (
                        f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl)
                    )
        return out


def _rrf_fuse(rankings: list, k: int = RRF_K, weights: tuple | None = None) -> dict:
    """rankings = [(ranked_index_list, weight), ...] fused via weighted Reciprocal Rank Fusion."""
    scores = defaultdict(float)
    for ranking, weight in zip(rankings, weights or [1] * len(rankings)):
        for pos, idx in enumerate(ranking):
            scores[idx] += weight / (k + pos + 1)
    return scores


class Retriever:
    def __init__(self):
        self.docs = _load_docs()
        if not self.docs:
            raise RuntimeError("No data files found - run scraper first")
        self.texts = [_norm(_doc_text(d)) for d in self.docs]
        self.token_lists = [_tokens(t) for t in self.texts]
        self.doc_token_sets = [set(t) for t in self.token_lists]
        self.vocab = set()
        for t in self.token_lists:
            self.vocab.update(t)

        self.bm25 = _BM25(self.token_lists)

        from sentence_transformers import SentenceTransformer

        self.embedder = SentenceTransformer(SEMANTIC_MODEL)
        self.sem_matrix = self.embedder.encode(
            self.texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
        )

        self.cities = sorted(
            {str(d.get("city", "")) for d in self.docs if d.get("city") and d.get("city") != "Not available"},
            key=len,
            reverse=True,
        )

        # Normalized record names, for exact-name queries like "What is DG1?".
        self.name_keys = [
            _norm(str(d.get("name") or d.get("title") or "")).strip() for d in self.docs
        ]

    def _query_tokens(self, query: str) -> list:
        return [t for t in _tokens(query) if t not in STOPWORDS and (len(t) > 1 or t.isdigit())]

    def _fuzzy_vocab(self, token: str) -> list:
        if token in self.vocab:
            return [token]
        return [v for v in self.vocab if abs(len(v) - len(token)) <= 1 and _lev1(token, v) <= 1]

    def _matched_city(self, query: str) -> str:
        q = query.lower()
        for city in self.cities:
            if city.lower() in q:
                return city
        return ""

    def _query_types(self, query: str) -> list:
        """Canonical Type words demanded by the query, e.g. ['villa'].

        Fuzzy-aware (vila -> villa) so the hard Type filter works on typos too.
        When the query names no hard property kind, semantic phrases are mapped:
        'big house' / 'family house' / 'large house' -> villa.
        """
        out = []
        for t in self._query_tokens(_norm(query or "")):
            if t in HARD_TYPE_WORDS:
                canon = TYPE_SYNONYMS.get(t, t)
            else:
                found = next((v for v in self._fuzzy_vocab(t) if v in HARD_TYPE_WORDS), "")
                canon = TYPE_SYNONYMS.get(found, found) if found else ""
            if canon and canon not in out:
                out.append(canon)
        if not out:
            q = (query or "").lower()
            for pattern, canon in SEMANTIC_TYPE_PHRASES:
                if re.search(pattern, q):
                    out.append(canon)
                    break
        return out

    def _coverage(self, q_tokens: list, doc_tokens: set) -> float:
        if not q_tokens:
            return 0.0
        hit = 0
        for t in q_tokens:
            if t in doc_tokens or any(_lev1(t, d) <= 1 for d in doc_tokens):
                hit += 1
        return hit / len(q_tokens)

    def query_info(self, query: str) -> dict:
        """Diagnostics used by the chat layer for out-of-scope decisions."""
        translated = _translate(query or "")
        norm = _norm(translated)
        arabic_left = bool(re.search(r"[\u0600-\u06FF]", translated))
        toks = self._query_tokens(norm)
        unknown = [t for t in toks if not self._fuzzy_vocab(t)]
        ratio = (len(unknown) / len(toks)) if toks else 1.0
        return {"arabic_left": arabic_left, "unknown_ratio": ratio, "tokens": toks}

    def semantic_nearest(self, query: str, n: int = 3, source: str = "") -> list:
        """Top-n by pure semantic similarity (used for 'similar properties')."""
        q_norm = _norm(_translate(query or ""))
        if not q_norm.strip():
            return []
        q_emb = self.embedder.encode([q_norm], normalize_embeddings=True)
        sims = self.sem_matrix @ q_emb[0]
        idxs = list(range(len(self.docs)))
        if source:
            idxs = [i for i in idxs if self.docs[i].get("_source") == source]
        lt = _listing_type_filter(q_norm)
        if lt:
            idxs = [
                i for i in idxs
                if str(self.docs[i].get("listing_type") or "").lower() == lt
            ]
        qts = set(self._query_types(q_norm))
        if qts:
            idxs = [i for i in idxs if _doc_type_matches(self.docs[i], qts)]
        specs = parse_query_specs(query)
        if specs:
            idxs = [i for i in idxs if _specs_match(self.docs[i], specs)]
        idxs.sort(key=lambda i: -sims[i])
        out = []
        for i in idxs[: max(n * 2, 6)]:
            if sims[i] <= 0:
                continue
            rec = dict(self.docs[i])
            rec["score"] = round(float(sims[i]), 4)
            out.append(rec)
            if len(out) >= n:
                break
        return out

    def search(self, query: str, top_k: int = 5) -> list:
        query = (query or "").strip()
        if not query:
            return []

        translated = _translate(query)
        query_norm = _norm(translated)
        q_tokens = self._query_tokens(query_norm)
        if not q_tokens:
            return []

        src = _source_filter(query_norm)
        city = self._matched_city(query_norm)
        listing_type = _listing_type_filter(query_norm)
        type_words = set(self._query_types(query_norm))
        specs = parse_query_specs(query)
        # Exact record name in the query ("What is DG1?") -> that record only.
        name_hits = _exact_name_hits(query, self.name_keys)

        # Global unknown-entity gate: e.g. "Mars pe plot" -> empty
        unknown = [t for t in q_tokens if not self._fuzzy_vocab(t)]
        if not name_hits and len(unknown) / len(q_tokens) >= 0.5 and not city and not src:
            return []

        # BM25 query terms with fuzzy expansion (vila -> villa)
        bm25_terms: list = []
        for t in q_tokens:
            for v in self._fuzzy_vocab(t):
                if v not in bm25_terms:
                    bm25_terms.append(v)

        if name_hits:
            # The name identifies the entity: no source / city / type narrowing,
            # so a DarGlobal project never pulls in Wasalt rows (and vice versa).
            candidates = list(name_hits)
        else:
            candidates = list(range(len(self.docs)))
            if src:
                candidates = [i for i in candidates if self.docs[i].get("_source") == src]
            if city:
                candidates = [
                    i for i in candidates if str(self.docs[i].get("city", "")).lower() == city.lower()
                ]
            if listing_type:
                candidates = [
                    i
                    for i in candidates
                    if str(self.docs[i].get("listing_type") or "").lower() == listing_type
                ]
            if type_words:
                candidates = [i for i in candidates if _doc_type_matches(self.docs[i], type_words)]
        # Exact specs ("60 SQM", "1 Bedroom") are a HARD filter: never pad with
        # 50/70 SQM or 2/3 Bedroom rows just to fill top_k.
        if specs:
            candidates = [i for i in candidates if _specs_match(self.docs[i], specs)]
        if not candidates:
            return []

        bm25_scores = self.bm25.scores(bm25_terms)
        q_emb = self.embedder.encode([query_norm], normalize_embeddings=True)
        sem_scores = self.sem_matrix @ q_emb[0]

        bm25_rank = sorted(candidates, key=lambda i: -bm25_scores[i])
        sem_rank = sorted(candidates, key=lambda i: -sem_scores[i])
        rrf = _rrf_fuse([bm25_rank, sem_rank], weights=(2.0, 1.0))
        # Demote hub/category pages (no real city) below actual properties.
        for i in list(rrf):
            city_val = str(self.docs[i].get("city") or "")
            if not city_val or city_val == "Not available":
                rrf[i] *= 0.6

        # Hardest query token = lowest idf among its fuzzy variants (rarest real term);
        # non-city docs must match it.
        hardest = ""
        hardest_idf = -1.0
        for t in q_tokens:
            fuzzy = self._fuzzy_vocab(t)
            if not fuzzy:
                continue
            tidf = min(self.bm25.idf.get(v, 0.0) for v in fuzzy)
            if tidf > hardest_idf:
                hardest, hardest_idf = t, tidf

        # City queries with an explicit property type must match that type (fuzzy-aware).
        # A mapped type ("big house" -> villa) replaces the raw token list, otherwise
        # the raw word "house" would reject every Villa record.
        if type_words:
            prop_q = list(type_words)
        else:
            prop_q = [
                t for t in q_tokens
                if any(v in PROPERTY_TYPES for v in self._fuzzy_vocab(t))
            ]

        ordered = sorted(rrf, key=lambda i: -rrf[i])
        strict, loose = [], []
        for idx in ordered:
            ok = True
            if not city:
                if hardest and self._coverage([hardest], self.doc_token_sets[idx]) < 1.0:
                    ok = False
                elif self._coverage(q_tokens, self.doc_token_sets[idx]) < MIN_COVERAGE:
                    ok = False
                elif bm25_scores[idx] <= 0 and sem_scores[idx] < MIN_SEM:
                    ok = False
            else:
                if prop_q and self._coverage(prop_q, self.doc_token_sets[idx]) <= 0:
                    ok = False
            (strict if ok else loose).append(idx)

        # Strict matches first; fill remaining slots from loose so >= top_k results.
        # Specific query (exact area/bedroom, or an exact record name): every
        # candidate is already an exact match, so rank them directly and NEVER
        # pad with looser rows.
        if specs or name_hits:
            results = ordered[:top_k]
        else:
            results = strict[:top_k]
            if results:
                for idx in loose:
                    if len(results) >= top_k:
                        break
                    results.append(idx)
        results = [(i, rrf[i]) for i in results]

        out = []
        for idx, score in results:
            rec = dict(self.docs[idx])
            rec["score"] = round(float(score), 5)
            out.append(rec)
        return out


_retriever = Retriever()


def search(query: str, top_k: int = 5) -> list:
    return _retriever.search(query, top_k=top_k)


def query_info(query: str) -> dict:
    return _retriever.query_info(query)


def query_type_filter(query: str) -> list:
    """Canonical Type words demanded by the query (e.g. ['villa']), for headers."""
    return _retriever._query_types(_translate(query or ""))


def query_specs(query: str) -> dict:
    """Exact numeric specs in the query (e.g. {'area_sqm': 60.0, 'bedrooms': 1})."""
    return parse_query_specs(query)


def semantic_nearest(query: str, n: int = 3, source: str = "") -> list:
    return _retriever.semantic_nearest(query, n=n, source=source)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Riyadh me villa"
    for r in search(q):
        print(f"{r.get('_source')} | {r.get('city')} | {r.get('title') or r.get('name')} | score={r.get('score')}")
