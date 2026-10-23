# -*- coding: utf-8 -*-
"""
database.py - SQLite job history, application tracking & user feedback
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id          TEXT UNIQUE NOT NULL,
            title           TEXT,
            company         TEXT,
            location        TEXT,
            url             TEXT,
            source          TEXT,
            score           REAL,
            status          TEXT DEFAULT 'notified', -- 'notified', 'applied', 'skipped'
            feedback_reason TEXT,
            applied_at      TEXT,
            feedback_at     TEXT,
            seen_at         TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS run_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at          TEXT DEFAULT (datetime('now','localtime')),
            jobs_scanned    INTEGER,
            jobs_matched    INTEGER,
            jobs_applied    INTEGER,
            jobs_alerted    INTEGER
        );
    """)
    conn.commit()
    conn.close()


def is_seen(job_id: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM seen_jobs WHERE job_id=?", (job_id,)).fetchone()
    conn.close()
    return row is not None


def mark_seen(job: dict, status: str = "notified"):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO seen_jobs
                (job_id, title, company, location, url, source, score, status, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["id"], job["title"], job["company"],
            job.get("location", ""), job["url"], job.get("source", ""),
            job.get("score", 0), status,
            datetime.now().isoformat() if status == "applied" else None
        ))
        conn.commit()
    except Exception as e:
        print(f"[DB] Error marking job: {e}")
    finally:
        conn.close()


def update_job_status(job_id: str, status: str, reason: str = None) -> bool:
    """Updates job status when user clicks Applied or Skip button in Telegram."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        if status == "applied":
            conn.execute("""
                UPDATE seen_jobs
                SET status = ?, applied_at = ?, feedback_at = ?
                WHERE job_id = ?
            """, (status, now, now, job_id))
        else:
            conn.execute("""
                UPDATE seen_jobs
                SET status = ?, feedback_reason = ?, feedback_at = ?
                WHERE job_id = ?
            """, (status, reason, now, job_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Error updating status for {job_id}: {e}")
        return False
    finally:
        conn.close()


def get_job_by_id(job_id: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM seen_jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_applied_jobs(limit: int = 10) -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT title, company, location, score, seen_at
        FROM seen_jobs
        WHERE status = 'applied'
        ORDER BY applied_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_skipped_jobs(limit: int = 10) -> list:
    conn = get_conn()
    rows = conn.execute("""
        SELECT title, company, location, feedback_reason
        FROM seen_jobs
        WHERE status = 'skipped' AND feedback_reason IS NOT NULL
        ORDER BY feedback_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_learning_context() -> str:
    """Generates dynamic few-shot feedback text for Gemini to learn from Sandeep's real decisions."""
    applied = get_applied_jobs(limit=5)
    skipped = get_skipped_jobs(limit=6)

    lines = []
    if applied:
        lines.append("CANDIDATE RECENTLY APPLIED TO (Positively model these):")
        for j in applied:
            lines.append(f"  + {j['title']} @ {j['company']} ({j['location']})")
    
    if skipped:
        lines.append("CANDIDATE REJECTED / DISQUALIFIED (Strictly penalize/avoid these patterns):")
        for j in skipped:
            reason = j.get('feedback_reason', 'Not specified')
            lines.append(f"  - {j['title']} @ {j['company']} (Reason: {reason})")

    return "\n".join(lines) if lines else "No previous candidate feedback recorded yet."


def log_run(scanned: int, matched: int, applied: int, alerted: int):
    conn = get_conn()
    conn.execute("""
        INSERT INTO run_log (jobs_scanned, jobs_matched, jobs_applied, jobs_alerted)
        VALUES (?, ?, ?, ?)
    """, (scanned, matched, applied, alerted))
    conn.commit()
    conn.close()
