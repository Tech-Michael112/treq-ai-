
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
                }
    return table

HS_TABLE = load_hs_table()

def retrieve_candidates(user_text, level=4, limit=40):
    

    stop = {"i", "a", "an", "the", "for", "in", "of", "need", "want",
            "hs", "code", "codes", "me", "get", "find", "give", "some",
            "usa", "us", "buyers", "sellers"}
    words = [w.strip(",.").lower() for w in user_text.split()]
    words = [w for w in words if len(w) > 2 and w not in stop]

    hits = []
    for code, info in HS_TABLE.items():
        if level and info["level"] != level:
            continue
        desc = info["description"].lower()
        if any(w in desc for w in words):
            hits.append({"code": code, "description": info["description"]})
    return hits[:limit]

def build_grounded_prompt(user_text, candidates):

    lines = [f"{c['code']} - {c['description']}" for c in candidates]
    code_block = "\n".join(lines) if lines else "(no matching codes found)"

    system = (
        "You are an HS-code selector. You will be given a list of OFFICIAL HS "
        "codes with descriptions. Choose only the codes from this list that "
        "match the user's product. NEVER invent a code that is not in the list. "
        "Return the chosen codes as a comma-separated string in a JSON field "
        '"hs_code". If none match, return an empty string.\n\n'
        "OFFICIAL HS CODES YOU MAY CHOOSE FROM:\n"
        f"{code_block}"
    )
    return system, user_text

def validate_codes(codes):
    if isinstance(codes, str):
        codes = [c.strip() for c in codes.split(",")]
    valid, invalid = [], []
    for raw in codes:
        code = str(raw).strip()
        if not code:
            continue
        (valid if code in HS_TABLE else invalid).append(code)
    return {"valid": valid, "invalid": invalid}

def ask_ai_for_codes(user_text, llm_call):
    
    candidates = retrieve_candidates(user_text)
    system, user = build_grounded_prompt(user_text, candidates)

    raw = llm_call(system, user)

    return system, user, candidates, raw

if __name__ == "__main__":

    user_text = "I need hs codes for carpets in usa"
    candidates = retrieve_candidates(user_text)

    print("USER ASKED:", user_text)
    print(f"\nRetrieved {len(candidates)} candidate codes from the file:")
    for c in candidates:
        print("  ", c["code"], "-", c["description"][:70])

    system, user = build_grounded_prompt(user_text, candidates)
    print("\n--- PROMPT THE MODEL WOULD RECEIVE (the 'attached memory') ---")
    print(system[:600], "...\n")
    print("The model now picks ONLY from the codes above, so it cannot")
    print("invent a code that isn't really in the carpet chapter.")
    