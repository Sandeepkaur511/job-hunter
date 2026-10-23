# -*- coding: utf-8 -*-
"""
main.py - Orchestrator with Dynamic Tier 2 Fallback:
1. Scrapes & scores Global Remote (USD/EUR, Worldwide & Relocation).
2. If < 3 relevant matches found, automatically activates Tier 2 (National Indian Remote/Hybrid).
3. Sends interactive cards with '✅ I Applied' and '❌ Skip' buttons to Telegram.
"""
import os
import sys

# Safe cross-platform UTF-8 reconfiguration
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Verify environment secrets before proceeding
REQUIRED_SECRETS = ["GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
missing = [s for s in REQUIRED_SECRETS if not os.getenv(s)]
if missing:
    print(f"\n[FATAL] Missing required environment secrets: {', '.join(missing)}", flush=True)
    print("Please add these in your repository Settings -> Secrets and variables -> Actions:", flush=True)
    print("https://github.com/Sandeepkaur511/job-hunter/settings/secrets/actions\n", flush=True)
    sys.exit(1)

from database import init_db, is_seen, mark_seen, log_run
import scrapers
from scorer import score_jobs
from notifier import send_daily_digest, send_message

MIN_SCORE = 7.0
MIN_DESIRED_MATCHES = 3


def run():
    print("\n" + "="*55, flush=True)
    print("  SANDEEP JOB AGENT - ADAPTIVE RUN (GLOBAL + INDIAN FALLBACK)", flush=True)
    print(f"  {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("="*55 + "\n", flush=True)

    init_db()

    # ─────────────────────────────────────────────────────────────
    # STEP 1: TIER 1 - GLOBAL REMOTE (Worldwide & Visa Relocation)
    # ─────────────────────────────────────────────────────────────
    print("STEP 1: Scanning Tier 1 Global Remote (USD/EUR, Worldwide)...", flush=True)
    tier1_jobs = []
    tier1_jobs += scrapers.scrape_jobicy()
    tier1_jobs += scrapers.scrape_remotive()
    tier1_jobs += scrapers.scrape_remoteok()

    # Deduplicate Tier 1
    new_tier1 = [j for j in tier1_jobs if not is_seen(j["id"])]
    print(f"  -> {len(new_tier1)} new Global Remote candidates to score", flush=True)

    matched_jobs = []
    if new_tier1:
        matched_jobs = score_jobs(new_tier1)
        for j in new_tier1:
            if j not in matched_jobs:
                mark_seen(j, status="skipped")

    print(f"\nTier 1 yielded {len(matched_jobs)} verified Global Remote matches (Score >= {MIN_SCORE}).", flush=True)

    # ─────────────────────────────────────────────────────────────
    # STEP 2: TIER 2 FALLBACK - NATIONAL INDIAN REMOTE & HYBRID
    # ─────────────────────────────────────────────────────────────
    tier2_jobs = []
    if len(matched_jobs) < MIN_DESIRED_MATCHES:
        print(f"\n[FALLBACK TRIGGERED] Seeking at least {MIN_DESIRED_MATCHES} jobs today. Fetching Indian National Remote & Hybrid...", flush=True)
        tier2_jobs = scrapers.scrape_indeed_india_remote()
        new_tier2 = [j for j in tier2_jobs if not is_seen(j["id"])]
        print(f"  -> {len(new_tier2)} new Indian Remote listings to evaluate", flush=True)

        if new_tier2:
            matched_india = score_jobs(new_tier2)
            matched_jobs.extend(matched_india)
            for j in new_tier2:
                if j not in matched_india:
                    mark_seen(j, status="skipped")

    total_scanned = len(tier1_jobs) + len(tier2_jobs)

    # ─────────────────────────────────────────────────────────────
    # STEP 3: RECORD MATCHES AND DISPATCH INTERACTIVE TELEGRAM CARDS
    # ─────────────────────────────────────────────────────────────
    for job in matched_jobs:
        mark_seen(job, status="notified")

    print(f"\nSTEP 3: Dispatching {len(matched_jobs)} interactive cards to Telegram...", flush=True)
    stats = {
        "scanned": total_scanned,
        "matched": len(matched_jobs),
        "applied": 0,
        "alerted": len(matched_jobs),
    }
    send_daily_digest(matched_jobs, [], stats)
    log_run(total_scanned, len(matched_jobs), 0, len(matched_jobs))

    print("\n" + "="*55, flush=True)
    print(f"  FINISHED  |  Total Scanned: {total_scanned}  |  Matched (7+): {len(matched_jobs)}", flush=True)
    print("="*55 + "\n", flush=True)


if __name__ == "__main__":
    run()
