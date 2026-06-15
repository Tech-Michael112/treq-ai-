"""
hs_search.py  --  the "intelligence" that picks HS codes from your CSV.

Drop this next to your Flask app. Point HS_CSV_PATH at your file.
It loads the codes once, then search_codes(text) returns the codes that
match whatever the user is talking about -- ready to feed to the AI.

CSV must have a code column and a description column. Defaults match the
WCO file (columns: hscode, description, level). Change the names below
if yours differ.
"""

import csv
import re
import os

HS_CSV_PATH = os.path.join(os.path.dirname(__file__), "harmonized-system.csv")
CODE_COL = "hscode"
DESC_COL = "description"
LEVEL_COL = "level"          # optional; set to None if your file has no level column

# words that carry no product meaning -- ignored when matching
STOPWORDS = {
    "i", "a", "an", "the", "for", "in", "of", "to", "and", "or", "is", "are",
    "need", "want", "get", "find", "give", "me", "my", "some", "any", "please",
    "hs", "hsn", "code", "codes", "tariff", "product", "products", "import",
    "export", "buyer", "buyers", "seller", "sellers", "supplier", "suppliers",
    "country", "what", "which", "show", "list", "looking", "about",
}


def _load(path=HS_CSV_PATH):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            code = str(r[CODE_COL]).strip()
            desc = str(r[DESC_COL]).strip()
            if not code:
                continue
            level = None
            if LEVEL_COL and LEVEL_COL in r and str(r[LEVEL_COL]).isdigit():
                level = int(r[LEVEL_COL])
            rows.append({
                "code": code,
                "description": desc,
                "desc_lower": desc.lower(),
                "level": level,
            })
    return rows


# load once at import
HS_ROWS = _load()


def _variants(word):
    """Return the word plus simple singular/plural forms so 'carpet'
    matches 'carpets', 'boxes' matches 'box', etc."""
    forms = {word}
    if word.endswith("ies") and len(word) > 4:
        forms.add(word[:-3] + "y")          # batteries -> battery
    if word.endswith("es") and len(word) > 3:
        forms.add(word[:-2])                # boxes -> box
    if word.endswith("s") and len(word) > 3:
        forms.add(word[:-1])                # carpets -> carpet
    forms.add(word + "s")                   # carpet -> carpets
    if word.endswith("y") and len(word) > 3:
        forms.add(word[:-1] + "ies")        # battery -> batteries
    return forms


def _keywords(text):
    """Pull meaningful product words out of the user's message,
    expanded with singular/plural variants."""
    words = re.findall(r"[a-z]+", text.lower())
    words = [w for w in words if len(w) > 2 and w not in STOPWORDS]
    expanded = set()
    for w in words:
        expanded |= _variants(w)
    return list(expanded)


def search_codes(text, level=4, limit=15):
    """
    Return the HS codes that best match the user's message.

    level : 2, 4, or 6 to restrict to that digit-level; None = all levels.
            (4 = headings, the level your trade DB usually filters on.)
    limit : max number of codes to return.

    Matching uses WHOLE-WORD matching so 'tire' won't match 'enTIREly'.
    It scans ALL levels for the keywords, then rolls each match UP to the
    requested `level` (e.g. a hit on 630260 'terry towelling' surfaces the
    4-digit heading 6302). This stops real headings being missed just
    because the matching word only appears in a deeper sub-line.
    """
    kws = _keywords(text)
    if not kws:
        return []

    patterns = [(kw, re.compile(r"\b" + re.escape(kw) + r"\b")) for kw in kws]

    # score every row at every level
    heading_score = {}   # rolled-up code -> best hit count
    for row in HS_ROWS:
        # skip chapter-level (2-digit) rows; we want headings or deeper
        if row["level"] is not None and row["level"] < 4:
            continue
        hits = sum(1 for _, pat in patterns if pat.search(row["desc_lower"]))
        if not hits:
            continue
        # roll this match up to the requested digit-level
        if level is None:
            key = row["code"]
        else:
            key = row["code"][:level]
        # keep the strongest hit count seen for that heading
        if hits > heading_score.get(key, 0):
            heading_score[key] = hits

    if not heading_score:
        return []

    # map each rolled-up code back to its official row (description at that level)
    by_code = {r["code"]: r for r in HS_ROWS}
    results = []
    for code, score in heading_score.items():
        row = by_code.get(code)
        if row is None:
            continue  # heading not present at that level in the file
        results.append((score, row))

    results.sort(key=lambda x: (-x[0], len(x[1]["code"]), x[1]["code"]))
    return [{"code": r["code"], "description": r["description"]}
            for _, r in results[:limit]]


def build_context_block(matches):
    """Format matched codes for injection into the AI prompt."""
    if not matches:
        return ""
    lines = [f"{m['code']} - {m['description']}" for m in matches]
    return "\n".join(lines)


def is_valid_code(code):
    """True if an exact code exists in the file (final safety check)."""
    code = str(code).strip()
    return any(r["code"] == code for r in HS_ROWS)


if __name__ == "__main__":
    print(f"Loaded {len(HS_ROWS)} HS codes from {os.path.basename(HS_CSV_PATH)}\n")
    for q in ["I need hs codes for carpets in usa",
              "looking for coffee buyers",
              "what is the code for car tyres",
              "honey exporters"]:
        print("Q:", q)
        for m in search_codes(q, level=4, limit=5):
            print("   ", m["code"], "-", m["description"][:65])
        print()
