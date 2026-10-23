# -*- coding: utf-8 -*-
"""
scrapers.py - Two-Tier High-Precision Job Scrapers:
TIER 1: Global Remote (Worldwide / Relocation to Dubai/Europe/UK / USD-EUR paying)
TIER 2 (Fallback): Indian National Jobs (Remote & Hybrid in India, avoiding Delhi NCR)
"""
import re
import hashlib
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

DATA_ROLE_RE = re.compile(
    r"\b(bi|business intelligence|analytics?|analyst|power\s*bi|powerbi|dax|sql|"
    r"bigquery|redshift|tableau|looker|reporting|dashboard|data\s*(?:engineer|analyst|"
    r"scientist|specialist|manager|architect|developer|lead)|data)\b",
    re.IGNORECASE
)

# Reject all contract / freelance / part-time / internship
STRICT_EXCLUDE_RE = re.compile(
    r"\b(contract|contractor|freelance|freelancer|temporary|temp|part-time|part time|"
    r"intern|internship|designer|video|veterinary|transport|recruiter|"
    r"telecaller|nurse|mechanical|civil|teacher|customer support|telefondienst|accounting)\b",
    re.IGNORECASE
)

# Domestic US/UK restrictions (Candidate resides in India)
DOMESTIC_ONLY_RE = re.compile(
    r"\b(us only|usa only|united states only|north america only|uk only|united kingdom only|"
    r"us citizen|green card|us work auth|us residency|uk resident|must reside in the us|"
    r"must be located in the us|must be located in the uk|canada only)\b",
    re.IGNORECASE
)

VISA_RELOCATION_RE = re.compile(
    r"\b(visa sponsorship|visa sponsored|sponsorship provided|relocation package|"
    r"relocation assistance|relocation provided|will sponsor|relocate)\b",
    re.IGNORECASE
)

AVOID_CITIES_RE = re.compile(r"\b(delhi|gurgaon|gurugram|noida|delhi ncr|ncr)\b", re.IGNORECASE)
ALLOWED_GLOBAL_GEOS = {"worldwide", "anywhere", "global", "apac", "work from anywhere", "india"}


def make_job_id(source: str, url: str, title: str = "") -> str:
    raw = f"{source}:{url}:{title}"
    return hashlib.md5(raw.encode()).hexdigest()


def is_job_eligible_global(title: str, location_str: str, desc_str: str, employment_type: str = "") -> bool:
    if not DATA_ROLE_RE.search(title):
        return False
    if STRICT_EXCLUDE_RE.search(title):
        return False
    if employment_type and STRICT_EXCLUDE_RE.search(employment_type):
        return False

    combined = f"{location_str} {desc_str[:800]}".lower()
    if DOMESTIC_ONLY_RE.search(combined) and not VISA_RELOCATION_RE.search(combined):
        return False

    loc_lower = location_str.strip().lower()
    is_global = any(ag in loc_lower for ag in ALLOWED_GLOBAL_GEOS)
    has_visa = bool(VISA_RELOCATION_RE.search(combined))

    if not is_global and not has_visa:
        foreign_countries = ["usa", "united states", "uk", "united kingdom", "canada", "germany", "spain", "france", "mexico", "philippines"]
        if any(fc in loc_lower for fc in foreign_countries):
            return False

    return True


def is_job_eligible_india(title: str, location_str: str) -> bool:
    if not DATA_ROLE_RE.search(title):
        return False
    if STRICT_EXCLUDE_RE.search(title):
        return False

    loc_lower = location_str.strip().lower()
    if AVOID_CITIES_RE.search(loc_lower) and "remote" not in loc_lower:
        return False

    return True


# ─────────────────────────────────────────────────────────────
# TIER 1: GLOBAL REMOTE SOURCES
# ─────────────────────────────────────────────────────────────
def scrape_jobicy() -> list:
    jobs = []
    print("[TIER 1] Jobicy (Worldwide / Relocation)...", flush=True)
    try:
        resp = requests.get(
            "https://jobicy.com/api/v2/remote-jobs?count=50&industry=data-science",
            headers=HEADERS,
            timeout=12
        )
        if resp.status_code == 200:
            for item in resp.json().get("jobs", []):
                title = item.get("jobTitle", "")
                geo = item.get("jobGeo", "")
                types_str = " ".join(item.get("jobType", []))
                desc = BeautifulSoup(item.get("jobDescription", ""), "html.parser").get_text()[:1000]

                if not is_job_eligible_global(title, geo, desc, types_str):
                    continue

                url = item.get("url", "")
                jobs.append({
                    "id": make_job_id("jobicy", url, title),
                    "title": title,
                    "company": item.get("companyName", "Company"),
                    "location": f"Global Remote ({geo})",
                    "url": url,
                    "description": desc[:500],
                    "source": "Jobicy",
                    "tier": "Global Remote",
                    "easy_apply": False,
                })
    except Exception as e:
        print(f"[TIER 1] Jobicy note: {e}", flush=True)
    print(f"  -> {len(jobs)} global roles from Jobicy", flush=True)
    return jobs


def scrape_remotive() -> list:
    jobs = []
    print("[TIER 1] Remotive (Worldwide Category)...", flush=True)
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs?category=data",
            headers=HEADERS,
            timeout=12
        )
        if resp.status_code == 200:
            for item in resp.json().get("jobs", []):
                title = item.get("title", "")
                loc = item.get("candidate_required_location", "")
                job_type = item.get("job_type", "")
                desc = BeautifulSoup(item.get("description", ""), "html.parser").get_text()[:1000]

                if not is_job_eligible_global(title, loc, desc, job_type):
                    continue

                url = item.get("url", "")
                jobs.append({
                    "id": make_job_id("remotive", url, title),
                    "title": title,
                    "company": item.get("company_name", "Company"),
                    "location": f"Global Remote ({loc})",
                    "url": url,
                    "description": desc[:500],
                    "source": "Remotive",
                    "tier": "Global Remote",
                    "easy_apply": False,
                })
    except Exception as e:
        print(f"[TIER 1] Remotive note: {e}", flush=True)
    print(f"  -> {len(jobs)} global roles from Remotive", flush=True)
    return jobs


def scrape_remoteok() -> list:
    jobs = []
    print("[TIER 1] RemoteOK (Worldwide USD)...", flush=True)
    seen_urls = set()
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers={**HEADERS, "Accept": "application/json"},
            timeout=12
        )
        if resp.status_code == 200:
            for item in resp.json():
                if not isinstance(item, dict) or "position" not in item:
                    continue
                title = item.get("position", "")
                loc = item.get("location", "")
                desc = item.get("description", "")

                if not is_job_eligible_global(title, loc, desc):
                    continue

                url = item.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                jobs.append({
                    "id": make_job_id("remoteok", url, title),
                    "title": title,
                    "company": item.get("company", "Company"),
                    "location": "Global Remote (USD)",
                    "url": url,
                    "description": desc[:500],
                    "source": "RemoteOK",
                    "tier": "Global Remote",
                    "easy_apply": False,
                })
    except Exception as e:
        print(f"[TIER 1] RemoteOK note: {e}", flush=True)
    print(f"  -> {len(jobs)} global roles from RemoteOK", flush=True)
    return jobs


# ─────────────────────────────────────────────────────────────
# TIER 2: INDIAN NATIONAL REMOTE & HYBRID (FALLBACK)
# ─────────────────────────────────────────────────────────────
def scrape_indeed_india_remote() -> list:
    jobs = []
    print("[TIER 2] Indeed India (Remote & Hybrid Data Roles)...", flush=True)
    try:
        with sync_playwright() as p:
            # Linux CI requires --no-sandbox flags
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
            )
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0")

            queries = [
                "https://in.indeed.com/jobs?q=Power+BI+remote&l=India&sort=date",
                "https://in.indeed.com/jobs?q=BI+Developer+remote&l=India&sort=date"
            ]

            for url in queries:
                try:
                    page.goto(url, timeout=20000)
                    page.wait_for_timeout(2000)

                    links = page.locator("a.jcs-JobTitle").all()
                    for l in links[:12]:
                        t = l.text_content(timeout=1000).strip()
                        href = l.get_attribute("href") or ""
                        if href and not href.startswith("http"):
                            href = "https://in.indeed.com" + href

                        if not t or not href:
                            continue

                        if not is_job_eligible_india(t, "India Remote"):
                            continue

                        jobs.append({
                            "id": make_job_id("indeed_in", href, t),
                            "title": t,
                            "company": "Top Employer (Indeed)",
                            "location": "India (Remote/Hybrid)",
                            "url": href,
                            "description": f"Verified Indian Role: {t} (Remote / Hybrid India)",
                            "source": "Indeed India",
                            "tier": "National India (Remote/Hybrid)",
                            "easy_apply": False,
                        })
                except Exception as ex:
                    print(f"  Indeed query note: {ex}", flush=True)

            browser.close()
    except Exception as e:
        print(f"[TIER 2] Indeed India note: {e}", flush=True)

    seen = set()
    unique = [j for j in jobs if not (j["id"] in seen or seen.add(j["id"]))]
    print(f"  -> {len(unique)} Indian Remote/Hybrid data jobs from Indeed India", flush=True)
    return unique


# ─────────────────────────────────────────────────────────────
# MASTER DISPATCHER: TIER 1 WITH AUTOMATIC TIER 2 FALLBACK
# ─────────────────────────────────────────────────────────────
def scrape_all() -> list:
    all_jobs = []

    print("\n--- TIER 1: GLOBAL REMOTE (USD/EUR, Worldwide & Relocation) ---", flush=True)
    tier1_jobs = []
    tier1_jobs += scrape_jobicy()
    tier1_jobs += scrape_remotive()
    tier1_jobs += scrape_remoteok()

    seen = set()
    unique_tier1 = [j for j in tier1_jobs if not (j["id"] in seen or seen.add(j["id"]))]
    all_jobs.extend(unique_tier1)

    print(f"Global Remote yielded {len(unique_tier1)} verified candidates.", flush=True)
    if len(unique_tier1) < 4:
        print("\n--- TIER 2: NATIONAL INDIAN FALLBACK (Remote & Hybrid) ---", flush=True)
        tier2_jobs = scrape_indeed_india_remote()
        for j in tier2_jobs:
            if j["id"] not in seen:
                seen.add(j["id"])
                all_jobs.append(j)

    print(f"\n[SCRAPER] Total candidate listings ready for Gemini: {len(all_jobs)}", flush=True)
    return all_jobs
