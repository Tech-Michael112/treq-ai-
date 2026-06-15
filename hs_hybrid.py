"""
hs_hybrid.py 
"""

import hs_search
import hs_semantic

def search_codes(text, level=4, limit=15):
    
    kw = hs_search.search_codes(text, level=level, limit=limit)
    sem = hs_semantic.search_codes(text, level=level, limit=limit)

    seen = set()
    out = []

    for m in kw:
        if m["code"] not in seen:
            seen.add(m["code"])
            out.append({"code": m["code"], "description": m["description"]})

    for m in sem:
        if m["code"] not in seen:
            seen.add(m["code"])
            out.append({"code": m["code"], "description": m["description"]})

    return out[:limit]

def build_context_block(matches):
    if not matches:
        return ""
    return "\n".join(f"{m['code']} - {m['description']}" for m in matches)

if __name__ == "__main__":
    for q in ["towels", "car tyres", "rug", "carpets", "coffee", "honey", "carpetts"]:
        codes = [m["code"] for m in search_codes(q)]
        print(f"{q:12} -> {codes}")
