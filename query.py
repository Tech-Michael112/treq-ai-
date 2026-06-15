
from exim_api import fetch_profiles

def fetch_and_format(params):

    product = (params.get("product") or "").strip()
    country = (params.get("country") or "").strip()
    kind    = (params.get("type") or "buyers").strip()
    page    = params.get("page") or 1

    if not product or not country:
        return None

    result = fetch_profiles(product, country, kind=kind, page=page)

    if result["error"]:
        return f" Couldn't fetch data: {result['error']}"

    total = result["total"]
    companies = result["companies"]
    if not companies:
        return (f"No {kind} found for \"{product}\" in {country.title()}. "
                f"This country may not have company-level data available.")

    from urllib.parse import quote
    per_page = 25
    start_n = (int(page) - 1) * per_page
    end_n = start_n + len(companies)
    header = (f"**{kind.title()} of \"{product}\" in {country.title()}**  —  "
              f"{total:,} total found, showing {start_n+1}–{end_n}:\n")
    lines = []
    for i, c in enumerate(companies):
        n = start_n + i + 1
        mid = c.get("master_id")
        name = c.get("name") or "Unknown"
        if mid:
            url = (f"/company/{mid}?name={quote(name)}"
                   f"&hs={quote(product)}&country={quote(country)}&kind={quote(kind)}")
            lines.append(f"{n}. [{name}]({url})")
        else:
            lines.append(f"{n}. {name}")
    footer = f"\n\n_Tap a company to see contacts & similar sellers. Say \"page {int(page)+1}\" for more._"
    return header + "\n".join(lines) + footer

def format_hs_codes(product):

    from hs_hybrid import search_codes
    product = (product or "").strip()

    JUNK = {"this", "that", "it", "to", "data", "code", "codes", "the", "one", "these"}
    words = [w for w in product.lower().split() if w not in JUNK]
    if not words:
        return ("I'm not sure which product you mean. Name the product you want "
                "the HS code for, e.g. \"coffee\" or \"carpets\".")
    matches = search_codes(" ".join(words), level=4, limit=12)
    if not matches:
        return f"I couldn't find an HS code for \"{product}\". Try describing it differently."
    lines = [f"**{m['code']}** — {m['description']}" for m in matches[:8]]
    return (f"HS codes related to \"{product}\":\n" + "\n".join(lines) +
            "\n\n_These are international 4-digit headings. Verify the exact code with local customs._")
