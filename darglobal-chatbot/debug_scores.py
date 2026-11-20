import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from app.retriever import _retriever as R, _norm, _translate, _source_filter

for q in ["DarGlobal ke Dubai projects dikhao", "Mujhe bada ghar chahiye Riyadh me"]:
    t = _translate(q)
    n = _norm(t)
    print("=" * 60)
    print("Q:", q)
    print("norm:", n)
    print("source filter:", repr(_source_filter(n)), "| city:", repr(R._matched_city(n)))
    cands = list(range(len(R.docs)))
    src = _source_filter(n)
    if src:
        cands = [i for i in cands if R.docs[i]["_source"] == src]
    city = R._matched_city(n)
    if city:
        cands = [i for i in cands if str(R.docs[i].get("city", "")).lower() == city.lower()]
    print("candidates:", len(cands))
    qv = R.vectorizer.transform([n])
    kw = (R.matrix[cands] @ qv.T).toarray().ravel()
    qe = R.embedder.encode([n], normalize_embeddings=True)
    sem = R.sem_matrix[cands] @ qe[0]
    comb = 0.5 * kw + 0.5 * np.clip(sem, 0, None)
    order = np.argsort(-comb)[:6]
    for j in order:
        i = cands[j]
        d = R.docs[i]
        print(
            "  kw=%.3f sem=%.3f comb=%.3f | %s | %s | %s"
            % (kw[j], sem[j], comb[j], d["_source"], d.get("city"), d.get("name") or d.get("title"))
        )
