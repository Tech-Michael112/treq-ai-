

import os
import json
import time
import requests

BASE = "https://pkvvcly41h.execute-api.us-east-1.amazonaws.com/snfapi-exim"
GET_PROFILES_URL = f"{BASE}/lead_maps/get_profiles"
TOKEN_URL        = f"{BASE}/authorization/generate_access_token"
VALIDATE_URL     = f"{BASE}/login/validate"
BASIC_INFO_URL   = f"{BASE}/company_profile/basic_info"
PEOPLE_URL       = f"{BASE}/company_profile/get_company_people"
SIMILAR_URL      = f"{BASE}/company_profile/similar_buyers"
ANALYSIS_URL     = f"{BASE}/company_profile/main_product_analysis"
ADD_LEAD_URL     = f"{BASE}/lead_maps/add_lead"
ABOUT_URL        = f"{BASE}/company_profile/about_us"
MAIN_PRODUCTS_URL = f"{BASE}/company_profile/main_products_data"

EXIM_API_KEY  = os.environ.get("EXIM_API_KEY",  "X7WeW8Lp4M6orTTQLFS4i27GzhoPlD4099utjdI8")
EXIM_CLIENT_ID = os.environ.get("EXIM_CLIENT_ID", "358ap8l1i7ehil05cp1v9lsr5b")
EXIM_EMAIL    = os.environ.get("EXIM_EMAIL",    "michael@gtaindia.org")
EXIM_PASSWORD = os.environ.get("EXIM_PASSWORD", "Michael@1303")
EXIM_FCM      = os.environ.get("EXIM_FCM",
    "cpSNBCDLQLyMWmWRG7MMOi:APA91bGEaCSgscdnYny3N0T23x3KOEdpJxPSGKObVMPp-iGtYnFjwqDnPB6uVoNTEJKW9MVa3hCfOfXKz-YIBGvzUR4xXJl4ipFqstyevwXMYmzPY9MXTBw")

BASE_HEADERS = {
    "User-Agent": "Dart/3.12 (dart:io)",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "x-api-key": EXIM_API_KEY,
}

_session = {"auth_token": None, "token_id": None, "id": None, "expires_at": 0}

def _login():
    
    r = requests.post(TOKEN_URL,
                      data=json.dumps({"client_id": EXIM_CLIENT_ID,
                                       "grant_type": "refresh_token"}),
                      headers=BASE_HEADERS, timeout=20)
    r.raise_for_status()
    j = r.json()
    auth_token = j["auth_token"]
    expires_in = j.get("expires_in", 3600)

    hdr = {**BASE_HEADERS, "authenticate": auth_token}
    r2 = requests.post(VALIDATE_URL,
                       data=json.dumps({"email": EXIM_EMAIL,
                                        "password": EXIM_PASSWORD,
                                        "fcm_token": EXIM_FCM}),
                       headers=hdr, timeout=20)
    r2.raise_for_status()
    j2 = r2.json()

    _session["auth_token"] = auth_token
    _session["token_id"]   = j2["login_token"]
    _session["id"]         = j2.get("id", "129180")

    _session["expires_at"] = time.time() + max(60, expires_in - 60)
    return _session

def _ensure_session(force=False):
    if force or not _session["auth_token"] or time.time() >= _session["expires_at"]:
        _login()
    return _session

def fetch_profiles(product, country, kind="buyers", page=1,
                   range_start="2025-06-08", range_end="2026-06-07",
                   _retry=True):
    """
    FALSE
    """
    try:
        s = _ensure_session()
    except Exception as e:
        return {"total": 0, "companies": [], "error": f"Login failed: {e}"}

    payload = {
        "id": s["id"],
        "token_id": s["token_id"],
        "hscode": product,
        "type": kind,
        "selected_type": kind,
        "range_start": range_start,
        "range_end": range_end,
        "year": "",
        "country": country.lower(),
        "ser_name": "",
        "sort": "value",
        "order": "desc",
        "nt": "", "ex": "", "mi": "",
        "adv_search": "0",
        "sub_countries": "",
        "page": page,
    }
    hdr = {**BASE_HEADERS, "authenticate": s["auth_token"]}

    try:
        r = requests.post(GET_PROFILES_URL, data=json.dumps(payload),
                          headers=hdr, timeout=30)
    except Exception as e:
        return {"total": 0, "companies": [], "error": f"Request failed: {e}"}

    if r.status_code in (401, 403) and _retry:
        try:
            _ensure_session(force=True)
        except Exception as e:
            return {"total": 0, "companies": [], "error": f"Re-login failed: {e}"}
        return fetch_profiles(product, country, kind, page,
                              range_start, range_end, _retry=False)

    if r.status_code in (401, 403):
        return {"total": 0, "companies": [], "error": f"Auth rejected (HTTP {r.status_code})."}
    if not r.ok:
        return {"total": 0, "companies": [], "error": f"HTTP {r.status_code}: {r.text[:150]}"}

    try:
        data = r.json().get("data", {})
    except Exception:
        return {"total": 0, "companies": [], "error": "Bad JSON from API."}

    rows = data.get("data", []) or []
    total = data.get("recordsTotal", 0)

    if total == 0 and not rows and _retry:
        _ensure_session(force=True)
        return fetch_profiles(product, country, kind, page,
                              range_start, range_end, _retry=False)

    companies = [{"master_id": x.get("master_id"), "name": x.get("name")} for x in rows]
    return {"total": total, "companies": companies, "error": None}

def _post(url, payload, _retry=True):
    
    s = _ensure_session()
    body = {"id": s["id"], "token_id": s["token_id"], **payload}
    hdr = {**BASE_HEADERS, "authenticate": s["auth_token"]}
    r = requests.post(url, data=json.dumps(body), headers=hdr, timeout=30)
    if r.status_code in (401, 403) and _retry:
        _ensure_session(force=True)
        return _post(url, payload, _retry=False)
    if not r.ok:
        return None
    try:
        return r.json()
    except Exception:
        return None

def fetch_company_profile(master_id, company_name, hscode, kind="buyers", source="all"):
    """
    
    """
    try:
        mid = int(str(master_id).strip())
    except Exception:
        return {"company": {}, "contacts": [], "similar": [], "stats": {},
                "error": "Bad company id."}

    hs_list = [hscode] if isinstance(hscode, str) and hscode.strip() else (hscode or [])

    prof_type = "import" if str(kind).lower().startswith("buy") else "export"
    src = (source or "all").lower()
    data_source  = "*"   if src == "all" else src
    basic_source = "all" if src == "all" else src

    _post(ADD_LEAD_URL, {
        "source": "company-search-app", "master_id": mid, "type": kind,
        "analysis_country": "", "ai_search": "", "analysis_type": "",
        "from": None, "to": None, "hscode": "",
    })

    def _basic(t):
        return _post(BASIC_INFO_URL, {
            "master_id": mid, "type": t, "company_name": company_name,
            "hscode": hs_list, "from": "", "to": "", "reporting_country": "",
            "adv_search": 0, "profile_source": "", "analysis_country": "",
            "ai_search": "", "analysis_type": "", "searchtype": "",
            "all_source": basic_source, "profile_country": "",
        })

    info = _basic(prof_type)
    used_type = prof_type
    if not info or not info.get("company_meta"):
        other = "export" if prof_type == "import" else "import"
        alt = _basic(other)
        if alt and alt.get("company_meta"):
            info, used_type = alt, other

    if not info:
        return {"company": {}, "contacts": [], "similar": [], "stats": {},
                "error": "Couldn't reach the profile service for this company.",
                "debug": "basic_info returned nothing (no response)."}

    meta       = info.get("company_meta", "")
    country    = info.get("country", "")
    start_date = info.get("start_date", "")
    end_date   = info.get("end_date", "") or info.get("max_date", "")
    flag       = info.get("country_flag_path", "")
    contacts_total = info.get("contacts_total", "")

    if not meta:
        return {"company": {}, "contacts": [], "similar": [], "stats": {},
                "error": None,
                "debug": ("ex-im returned no profile token (company_meta) for "
                          f"master_id={mid}, type tried=export/import. "
                          "This usually means the id from the search list isn't the "
                          "profile id ex-im expects. Raw keys returned: "
                          + ", ".join(sorted(info.keys())))}

    people = _post(PEOPLE_URL, {
        "master_id": mid, "company_name": company_name,
        "country": country, "company_meta": meta, "source": (data_source if data_source!="*" else ""),
    }) or {}
    pdata = (people.get("data") or {})
    cdata = pdata.get("company_data") or {}
    plist = pdata.get("company_people_data") or []

    contacts = [{
        "name":     p.get("name") or f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
        "title":    p.get("title", ""),
        "location": ", ".join([x for x in [p.get("city"), p.get("state"), p.get("country")] if x]),
        "linkedin": p.get("linkedin_url", ""),
        "photo":    p.get("photo_url", ""),
        "seniority": p.get("seniority", ""),
    } for p in plist]

    sim = _post(SIMILAR_URL, {
        "master_id": mid, "type": "export",
        "start_date": start_date, "search": "", "page": 1,
        "end_date": end_date, "source": data_source, "searchkey": hs_list,
        "order_dir": "desc", "order_by": "value", "company_meta": meta,
    }) or {}
    srows = ((sim.get("data") or {}).get("data")) or []
    similar = [{
        "master_id": s.get("master_id"),
        "name":      s.get("company_name", ""),
        "country":   s.get("country", ""),
        "shipments": s.get("shipments", ""),
        "value":     s.get("value", ""),
    } for s in srows]

    ana = _post(ANALYSIS_URL, {
        "master_id": mid, "type": used_type, "main_prod_series": 8,
        "source": data_source, "max_date": end_date, "company_meta": meta,
        "gmp_analysis": 0,
    }) or {}
    adata = ana.get("data") or {}
    months = adata.get("hs_code_analysis_categories") or []
    series = adata.get("hs_code_analysis") or []

    monthly = [0.0] * len(months)
    for s in series:
        for i, v in enumerate(s.get("data") or []):
            if i < len(monthly):
                try:
                    monthly[i] += float(v or 0)
                except Exception:
                    pass
    industries = [{
        "name":     (it.get("name") or "").strip(),
        "value":    float(it.get("shipment_value") or 0),
        "quantity": it.get("quantity", 0),
    } for it in (adata.get("industry_analysis") or [])]
    stats = {
        "months": [m.replace("-", " ") for m in months],
        "monthly": [round(x, 2) for x in monthly],
        "industries": industries,
        "has_data": any(monthly) or bool(industries),
    }

    about = ""
    ab = _post(ABOUT_URL, {
        "master_id": mid, "type": used_type, "company_name": company_name,
        "company_meta": meta,
    })
    if ab and isinstance(ab.get("data"), str):
        about = ab["data"].strip()

    mp = _post(MAIN_PRODUCTS_URL, {
        "master_id": mid, "type": used_type, "start_date": start_date,
        "main_prod_series": 8, "end_date": end_date, "source": data_source,
        "company_meta": meta, "gmp_data": 0,
    }) or {}
    pv = ((mp.get("data") or {}).get("product_value")) or []
    products = []
    for it in pv:
        desc = (it.get("desc") or "").strip()
        code = str(it.get("hs_code") or "").strip()

        label = desc
        if not label or label == f"({code})":
            label = f"HS {code}"
        products.append({"code": code, "desc": label,
                         "percent": it.get("percent", "")})

    company = {
        "name":     cdata.get("name") or company_name,
        "country":  country or cdata.get("country", ""),
        "flag":     flag,
        "website":  cdata.get("website_url", ""),
        "phone":    cdata.get("phone", ""),
        "email":    cdata.get("email", ""),
        "revenue":  cdata.get("organization_revenue", ""),
        "industry": cdata.get("industry", ""),
        "address":  cdata.get("address", ""),
        "linkedin": cdata.get("linkedin_url", ""),
        "founded":  cdata.get("founded_year", ""),
        "contacts_total": contacts_total,
        "hscode":   ", ".join(hs_list),
        "about":    about,
        "source":   src,
    }
    return {"company": company, "contacts": contacts, "similar": similar,
            "stats": stats, "products": products, "error": None}

if __name__ == "__main__":
    print("logging in + fetching towels/usa buyers...")
    res = fetch_profiles("towels", "united states", "buyers")
    print("error:", res["error"], "| total:", res["total"])
    for c in res["companies"][:10]:
        print("  ", c["name"])
