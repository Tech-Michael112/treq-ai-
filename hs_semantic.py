

import csv
import re
import math
import os
from collections import defaultdict, Counter

HS_CSV_PATH = os.path.join(os.path.dirname(__file__), "harmonized-system.csv")
CODE_COL, DESC_COL, LEVEL_COL = "hscode", "description", "level"

ALIASES = {
    "rug": "carpet floor covering",
    "rugs": "carpet floor covering",
    "phone": "telephone",
    "cellphone": "telephone",
    "tv": "television",
    "footwear": "footwear",
}

NGRAM_MIN, NGRAM_MAX = 3, 4

def _ngrams(text):
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    grams = []
    for tok in text.split():
        padded = f" {tok} "
        for n in range(NGRAM_MIN, NGRAM_MAX + 1):
            for i in range(len(padded) - n + 1):
                grams.append(padded[i:i + n])
    return grams

def _load():
    rows = []
    with open(HS_CSV_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            code = str(r[CODE_COL]).strip()
            if not code:
                continue
            level = int(r[LEVEL_COL]) if str(r.get(LEVEL_COL, "")).isdigit() else None
            rows.append({"code": code,
                         "description": str(r[DESC_COL]).strip(),
                         "level": level})
    return rows

HS_ROWS = _load()

def _build_index(rows):
    df = Counter()
    doc_grams = []
    for row in rows:
        grams = Counter(_ngrams(row["description"]))
        doc_grams.append(grams)
        for g in grams:
            df[g] += 1
    N = len(rows)
    idf = {g: math.log((N + 1) / (dfv + 1)) + 1 for g, dfv in df.items()}

    vectors = []
    for grams in doc_grams:
        vec = {g: (1 + math.log(c)) * idf[g] for g, c in grams.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append((vec, norm))
    return idf, vectors

_IDF, _VECTORS = _build_index(HS_ROWS)

def _query_vector(text):

    extra = []
    for w in re.findall(r"[a-z]+", text.lower()):
        if w in ALIASES:
            extra.append(ALIASES[w])
    full = text + " " + " ".join(extra)

    grams = Counter(_ngrams(full))
    vec = {g: (1 + math.log(c)) * _IDF.get(g, 0.0) for g, c in grams.items()}
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return vec, norm

def search_codes(text, level=4, limit=10, min_score=0.04):
    
    if not text.strip():
        return []
    qvec, qnorm = _query_vector(text)

    best = {}
    for row, (vec, norm) in zip(HS_ROWS, _VECTORS):
        if row["level"] is not None and level is not None and row["level"] < 4:

            continue

        if len(qvec) < len(vec):
            dot = sum(w * vec.get(g, 0.0) for g, w in qvec.items())
        else:
            dot = sum(w * qvec.get(g, 0.0) for g, w in vec.items())
        if dot <= 0:
            continue
        score = dot / (qnorm * norm)
        if score < min_score:
            continue
        key = row["code"][:level] if level else row["code"]
        if key not in best or score > best[key][0]:
            best[key] = (score, row)

    by_code = {r["code"]: r for r in HS_ROWS}
    out = []
    for key, (score, row) in best.items():
        head = by_code.get(key, row)
        out.append((score, head))
    out.sort(key=lambda x: -x[0])

    seen, results = set(), []
    for score, row in out:
        if row["code"] in seen:
            continue
        seen.add(row["code"])
        results.append({"code": row["code"],
                        "description": row["description"],
                        "score": round(score, 3)})
        if len(results) >= limit:
            break
    return results

def build_context_block(matches):
    if not matches:
        return ""
    return "\n".join(f"{m['code']} - {m['description']}" for m in matches)

if __name__ == "__main__":
    print(f"Indexed {len(HS_ROWS)} HS descriptions (char n-gram TF-IDF)\n")
    for q in ["towels", "carpets", "rug", "coffee", "car tyres", "honey", "carpetts"]:
        print("Q:", q)
        for m in search_codes(q, level=4, limit=6):
            print(f"   {m['code']}  ({m['score']})  {m['description'][:58]}")
        print()
