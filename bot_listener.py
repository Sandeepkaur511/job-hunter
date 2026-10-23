# -*- coding: utf-8 -*-
"""
bot_listener.py - Interactive Telegram Bot Listener
Handles inline button clicks (✅ Applied, ❌ Skip with reason), logs decisions into SQLite,
and powers the few-shot learning loop for Gemini.
"""
import os
import sys
import io
import time
import requests
import html
from datetime import datetime
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

import database
database.init_db()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

REASON_MAP = {
    "loc": "In-country remote only (Candidate in India - no visa/sponsorship)",
    "contract": "Contract / Freelance role (Candidate requires Full-Time)",
    "skills": "Irrelevant tech stack or domain",
    "level": "Salary or Seniority mismatch",
    "other": "Not interested / General mismatch"
}


def answer_callback(callback_id: str, text: str, show_alert: bool = False):
    try:
        requests.post(
            f"{BASE_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text, "show_alert": show_alert},
            timeout=10
        )
    except Exception as e:
        print(f"[BOT] Error answering callback: {e}", flush=True)


def edit_message(chat_id: int, message_id: int, new_text: str, reply_markup: dict = None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": new_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    else:
        payload["reply_markup"] = {"inline_keyboard": []}  # remove buttons

    try:
        requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=10)
    except Exception as e:
        print(f"[BOT] Error editing message: {e}", flush=True)


def handle_callback_query(cb: dict):
    callback_id = cb["id"]
    data = cb.get("data", "")
    message = cb.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    orig_text = message.get("text", "")

    print(f"[BOT] Action clicked: {data}", flush=True)

    # 1. User clicked "✅ I Applied"
    if data.startswith("apply:"):
        job_id = data.split(":", 1)[1]
        database.update_job_status(job_id, status="applied")
        answer_callback(callback_id, "🎉 Logged! Marked as Applied in your database.", show_alert=True)
        
        # Append applied status to the message
        updated_text = orig_text + f"\n\n<b>Status: ✅ APPLIED ({datetime.now().strftime('%d %b')})</b>"
        # Keep an inactive indicator button
        inactive_markup = {
            "inline_keyboard": [[{"text": "✅ Applied & Logged", "callback_data": "noop"}]]
        }
        edit_message(chat_id, message_id, updated_text, reply_markup=inactive_markup)

    # 2. User clicked "❌ Skip" -> present reason choices
    elif data.startswith("skip:"):
        job_id = data.split(":", 1)[1]
        answer_callback(callback_id, "Why are you skipping? Tap a reason to train the model:")
        
        reason_keyboard = {
            "inline_keyboard": [
                [{"text": "🌍 Domestic US/UK only (need global)", "callback_data": f"reason:loc:{job_id}"}],
                [{"text": "📝 Contract / Freelance role", "callback_data": f"reason:contract:{job_id}"}],
                [{"text": "🛠 Tech stack mismatch", "callback_data": f"reason:skills:{job_id}"}],
                [{"text": "💰 Salary / Level mismatch", "callback_data": f"reason:level:{job_id}"}],
                [{"text": "⏩ Other / Just Skip", "callback_data": f"reason:other:{job_id}"}]
            ]
        }
        edit_message(chat_id, message_id, orig_text, reply_markup=reason_keyboard)

    # 3. User selected a skip reason
    elif data.startswith("reason:"):
        parts = data.split(":")
        code = parts[1]
        job_id = parts[2]
        reason_label = REASON_MAP.get(code, "General mismatch")

        database.update_job_status(job_id, status="skipped", reason=reason_label)
        answer_callback(callback_id, "Recorded! Gemini learned to penalize this pattern in future scans.")

        updated_text = orig_text + f"\n\n<b>Status: ❌ SKIPPED</b>\n<i>Reason: {html.escape(reason_label)}</i>"
        edit_message(chat_id, message_id, updated_text, reply_markup=None)

    elif data == "noop":
        answer_callback(callback_id, "This job is already logged as Applied.")


def handle_message(msg: dict):
    text = msg.get("text", "").strip().lower()
    chat_id = msg.get("chat", {}).get("id")

    if text in ["/status", "/stats"]:
        applied = database.get_applied_jobs(limit=5)
        skipped = database.get_skipped_jobs(limit=5)
        
        resp = "<b>📊 Job Hunting Progress & Memory</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        resp += f"<b>Total Jobs Applied:</b> {len(applied)}\n"
        for j in applied:
            resp += f"  • {html.escape(j['title'])} @ {html.escape(j['company'])}\n"
        
        resp += f"\n<b>Recent Filtered/Skipped:</b> {len(skipped)}\n"
        for j in skipped:
            resp += f"  • {html.escape(j['title'])} ({html.escape(j.get('feedback_reason', ''))})\n"
        
        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": resp, "parse_mode": "HTML"})

    elif text in ["/help", "/start"]:
        help_text = (
            "<b>🤖 Sandeep's AI Job Agent</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "• Scans for 100% Global Remote / Relocation roles daily at <b>12:00 PM IST</b>.\n"
            "• Strict filters: Full-time only (no contract/freelance), Worldwide hire only.\n\n"
            "<b>Interactive Features:</b>\n"
            "• Tap <b>'✅ I Applied'</b> on any card to record the application in your DB.\n"
            "• Tap <b>'❌ Skip'</b> to provide feedback (Gemini learns to avoid similar jobs).\n"
            "• Type <b>/status</b> anytime to view your application history and learned preferences.\n"
        )
        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": help_text, "parse_mode": "HTML"})


def poll_updates():
    print("\n" + "="*50, flush=True)
    print("  TELEGRAM INTERACTIVE BOT LISTENER ACTIVE", flush=True)
    print("  Listening for button taps (Applied / Skip reasons)...", flush=True)
    print("="*50 + "\n", flush=True)

    offset = 0
    while True:
        try:
            resp = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 25},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1

                    if "callback_query" in update:
                        handle_callback_query(update["callback_query"])
                    elif "message" in update:
                        handle_message(update["message"])

        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"[BOT] Polling error: {e}", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    poll_updates()
