# -*- coding: utf-8 -*-
"""
notifier.py - Telegram bot notification sender with Interactive Inline Action Buttons
"""
import os
import html
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(text: str, parse_mode: str = "HTML", reply_markup: dict = None) -> bool:
    """Send a message to Sandeep's Telegram with optional inline keyboard buttons."""
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        resp = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=15)
        if resp.status_code == 200:
            return True
        else:
            print(f"[TELEGRAM] Error {resp.status_code}: {resp.text}", flush=True)
            return False
    except Exception as e:
        print(f"[TELEGRAM] Exception: {e}", flush=True)
        return False


def format_job_entry(job: dict, idx: int) -> tuple:
    score = job.get("score", 0)
    title = html.escape(str(job.get("title", "Unknown")))
    company = html.escape(str(job.get("company", "Company")))
    location = html.escape(str(job.get("location", "Global Remote")))
    url = job.get("url", "#")
    source = html.escape(str(job.get("source", "")))
    reason = html.escape(str(job.get("score_reason", "")))
    job_id = job.get("id", "")

    skills_raw = job.get("skills_matched", [])
    skills_str = ", ".join(html.escape(str(s)) for s in skills_raw[:4]) if skills_raw else "Power BI, SQL, Analytics"

    if score >= 9:
        score_badge = "[🔥 TOP MATCH 9+]"
    elif score >= 8:
        score_badge = "[⭐ STRONG MATCH 8+]"
    else:
        score_badge = "[✅ GOOD MATCH 7+]"

    msg_text = (
        f"<b>{idx}. {title}</b>\n"
        f"🏢 {company}  |  📍 {location}\n"
        f"📊 Match Score: <b>{score:.1f}/10</b> {score_badge}\n"
        f"💡 {reason}\n"
        f"🛠 Skills: {skills_str}\n"
        f"🔗 <a href=\"{url}\">Open & Apply Here</a>\n"
        f"🌐 Source: {source}"
    )

    markup = {
        "inline_keyboard": [
            [
                {"text": "✅ I Applied", "callback_data": f"apply:{job_id}"},
                {"text": "❌ Skip / Not for me", "callback_data": f"skip:{job_id}"}
            ]
        ]
    }

    return msg_text, markup


def send_daily_digest(matched_jobs: list, applied_jobs: list, stats: dict):
    """Send the full daily digest with interactive tracking buttons to Telegram."""
    date_str = datetime.now().strftime("%d %b %Y")
    total_scanned = stats.get("scanned", 0)
    total_matched = len(matched_jobs)

    header = (
        f"☀️ <b>DAILY JOB DIGEST - {date_str}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 Filtered Listings Scanned: {total_scanned}\n"
        f"🎯 High-Relevance Global Remote Matches: {total_matched}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Tap '✅ I Applied' or '❌ Skip' on each job below to log it and train your model.</i>"
    )
    send_message(header)

    if not matched_jobs:
        send_message(
            "📭 <b>No new 100% Global Remote / Full-Time jobs matched today.</b>\n"
            "Domestic-only and contract listings were rejected to save you time.\n"
            "The agent will scan again tomorrow at 12:00 PM IST."
        )
        return

    # Send each job with interactive action buttons
    for idx, job in enumerate(matched_jobs, 1):
        msg_text, markup = format_job_entry(job, idx)
        send_message(msg_text, reply_markup=markup)

    footer = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Digest completed for {date_str}.\n"
        f"Your clicks train Gemini's scoring engine for future scans."
    )
    send_message(footer)


def test_connection() -> bool:
    try:
        resp = requests.get(f"{BASE_URL}/getMe", timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
