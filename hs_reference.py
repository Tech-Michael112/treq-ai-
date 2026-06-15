
import csv

HS_CSV_PATH = "harmonized-system.csv"

def load_hs_table(path=HS_CSV_PATH):
   
    table = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = str(row["hscode"]).strip()
            if code:
                table[code] = {
                    "description": row["description"].strip(),
                    "level": int(row["level"]) if row["level"].isdigit() else None,
                    "section": row["section"].strip(),
                }
    return table

HS_TABLE = load_hs_table()

def search_hs(keyword, level=None, limit=20):
   
    kw = keyword.lower().strip()
    hits = []
    for code, info in HS_TABLE.items():
        if kw in info["description"].lower():
            if level is None or info["level"] == level:
                hits.append({"code": code, "level": info["level"],
                             "description": info["description"]})
    hits.sort(key=lambda h: (h["level"] or 99, h["code"]))
    return hits[:limit]

def is_real_code(code):
   
    return str(code).strip() in HS_TABLE

def validate_codes(codes, allow_prefix=True):

    if isinstance(codes, str):
        codes = [c.strip() for c in codes.split(",")]

    valid, invalid = [], []
    for raw in codes:
        code = str(raw).strip()
        if not code:
            continue
        if code in HS_TABLE:
            valid.append({"code": code, "description": HS_TABLE[code]["description"]})
        elif allow_prefix and any(k.startswith(code) for k in HS_TABLE):
            match = next(k for k in HS_TABLE if k.startswith(code))
            valid.append({"code": code, "description": HS_TABLE[match]["description"]})
        else:
            invalid.append(code)
    return {"valid": valid, "invalid": invalid}

def clean_ai_hscode_string(ai_hscode_string, allow_prefix=True):
    result = validate_codes(ai_hscode_string, allow_prefix=allow_prefix)
    good = [item["code"] for item in result["valid"]]
    return ", ".join(good), result["invalid"]

if __name__ == "__main__":
    print(f"Loaded {len(HS_TABLE)} HS codes\n")

    print("(B) search 'carpet' at 4-digit heading level:")
    for hit in search_hs("carpet", level=4):
        print(f"   {hit['code']}  {hit['description']}")

    print("\n(B) search 'tire' (all levels, first 8):")
    for hit in search_hs("tire", limit=8):
        print(f"   {hit['code']}  L{hit['level']}  {hit['description'][:60]}")

    print("\n(A) validate AI output '5701, 5702, 5703, 9999, 0000':")
    cleaned, bad = clean_ai_hscode_string("5701, 5702, 5703, 9999, 0000")
    print("   keep    ->", cleaned)
    print("   dropped ->", bad)
