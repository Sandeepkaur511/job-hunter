# -*- coding: utf-8 -*-
"""
test_setup.py - Verify all connections before first real run
"""
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

print("\n" + "="*55)
print("  SANDEEP JOB AGENT - SETUP TEST")
print("="*55 + "\n")

errors = []

# Test 1: Gemini API (new google-genai SDK)
print("1. Testing Gemini API (gemini-3.8-flash)...")
try:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(model="gemini-3.8-flash", contents="Reply with just: OK")
    if response.text and len(response.text) > 0:
        print(f"   PASS - Gemini API working! Response: {response.text.strip()[:50]}\n")
    else:
        raise Exception("Empty response from Gemini")
except Exception as e:
    print(f"   FAIL - Gemini API error: {e}\n")
    errors.append(f"Gemini: {e}")

# Test 2: Telegram Bot
print("2. Testing Telegram Bot...")
try:
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    if r.status_code == 200:
        bot_name = r.json()["result"]["username"]
        print(f"   Bot connected: @{bot_name}")

        msg = (
            "<b>Job Agent - Setup Test</b>\n\n"
            "Your job agent is configured and working!\n"
            "You will receive your daily job digest at <b>12:00 PM IST</b> every day.\n\n"
            "<i>Sandeep Job Agent v1.0</i>"
        )
        r2 = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        if r2.status_code == 200:
            print("   PASS - Test message sent to your Telegram! Check your phone.\n")
        else:
            resp_data = r2.json()
            err_desc = resp_data.get("description", r2.text)
            print(f"   WARN - Bot token works but message failed: {err_desc}")
            print("   --> Make sure you messaged @Sandiye_bot on Telegram first (press START)\n")
    else:
        raise Exception(f"HTTP {r.status_code}: {r.text}")
except Exception as e:
    print(f"   FAIL - Telegram error: {e}\n")
    errors.append(f"Telegram: {e}")

# Test 3: Database
print("3. Testing SQLite Database...")
try:
    from database import init_db, get_conn
    init_db()
    conn = get_conn()
    conn.execute("SELECT COUNT(*) FROM seen_jobs")
    conn.close()
    print("   PASS - Database initialized at jobs.db\n")
except Exception as e:
    print(f"   FAIL - Database error: {e}\n")
    errors.append(f"Database: {e}")

# Test 4: Quick scrape
print("4. Testing RemoteOK scraper (quick check)...")
try:
    from scrapers import scrape_remoteok
    jobs = scrape_remoteok()
    if jobs:
        sample = jobs[0]
        print(f"   PASS - RemoteOK returned {len(jobs)} jobs")
        print(f"   Sample: '{sample['title']}' @ {sample['company']}\n")
    else:
        print("   WARN - RemoteOK returned 0 jobs (may be rate-limited, not critical)\n")
except Exception as e:
    print(f"   FAIL - Scraper error: {e}\n")
    errors.append(f"Scrapers: {e}")

# Summary
print("="*55)
if not errors:
    print("ALL TESTS PASSED! Agent is ready to run.")
    print("")
    print("NEXT STEPS:")
    print("  Run first scan now:  py main.py")
    print("  Setup daily 12 PM:   Right-click setup_scheduler.ps1 -> Run with PowerShell")
else:
    print(f"{len(errors)} test(s) FAILED:")
    for err in errors:
        print(f"  - {err}")
    print("")
    if any("Gemini" in e for e in errors):
        print("  Gemini fix: Get a fresh key at https://aistudio.google.com/app/apikey")
    if any("Telegram" in e for e in errors):
        print("  Telegram fix: Open Telegram, search @Sandiye_bot, press START, then re-run")
print("="*55 + "\n")
