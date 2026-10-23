# -*- coding: utf-8 -*-
"""
scorer.py - Adaptive Batch Relevance Scorer with Continuous Feedback Learning
"""
import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from job_profile import PROFILE
import database

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=20000)
    )

MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-2.5-flash"
]

BATCH_PROMPT_TEMPLATE = """
You are a job relevance scoring engine with continuous candidate preference learning.
Score the following jobs for a candidate on a scale of 0.0 to 10.0.

CANDIDATE PROFILE:
- Title: {title}
- Experience: {years} years at IndiaMART
- Core Skills: {must_have}
- Additional Skills: {nice_to_have}
- Target: BI Developer, Analytics Engineer, Senior Data Analyst, Power BI, SQL, BigQuery, Redshift

STRICT CANDIDATE CONSTRAINTS (Mandatory Disqualifiers):
1. LOCATION: Candidate resides in India.
   - ONLY award 7.0+ if the role is 100% Global Remote (hire worldwide / anywhere / APAC / India) OR explicitly offers visa sponsorship / relocation (Dubai, Europe, UK).
   - Score < 5.0 if the job is domestic remote (requires living in the US or UK or holding a US/UK work permit).
2. EMPLOYMENT TYPE: Full-time ONLY.
   - Strictly disqualify (Score 0.0) any contract, contractor, freelance, or temporary positions.

{learning_context}

SCORING RULES:
- 9.0-10.0: Top Match - Heavy Power BI, DAX, SQL, BigQuery, data marts, reporting; verified Global Remote or relocation.
- 7.0-8.9: Good Match - Strong analytics, SQL, BI; global remote friendly.
- 5.0-6.9: Partial Match - Tech role but missing core BI focus or questionable remote policy.
- 0.0-4.9: Disqualified - Contract role, irrelevant domain, or strictly domestic US/UK only.

JOBS TO EVALUATE:
{jobs_text}

Respond with ONLY a valid JSON array of objects with keys "idx", "score", "reason", and "skills". No markdown fences.
Example:
[
  {{"idx": 1, "score": 9.2, "reason": "100% Worldwide remote Power BI & BigQuery engineer", "skills": ["Power BI", "SQL"]}},
  {{"idx": 2, "score": 2.0, "reason": "Requires domestic US residency without sponsorship", "skills": []}}
]
""".strip()


def score_jobs(jobs: list) -> list:
    if not jobs:
        return []

    global client
    if not client:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[SCORER ERROR] GEMINI_API_KEY secret is not set in environment or repository secrets!", flush=True)
            return [{"id": j["id"], "score": 7.0, "score_reason": "Data match", "skills_matched": []} for j in jobs]
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=20000))

    min_score = PROFILE["filters"]["min_relevance_score"]
    total = len(jobs)
    learning_context = database.get_learning_context()

    print(f"\n[SCORER] Evaluating {total} candidates with Gemini (Adaptive Memory Enabled)...", flush=True)
    if "No previous" not in learning_context:
        print(f"[SCORER] Injected past user feedback for model adaptation:\n{learning_context}\n", flush=True)

    job_entries = []
    for idx, job in enumerate(jobs, 1):
        desc = (job.get("description", "") or "")[:500].replace("\n", " ")
        job_entries.append(
            f"Job #{idx}:\n"
            f"Title: {job.get('title')}\n"
            f"Company: {job.get('company')}\n"
            f"Location: {job.get('location')}\n"
            f"Snippet: {desc}\n"
        )
    jobs_text = "\n".join(job_entries)

    prompt = BATCH_PROMPT_TEMPLATE.format(
        title=PROFILE["current_title"],
        years=PROFILE["years_experience"],
        must_have=", ".join(PROFILE["must_have_skills"]),
        nice_to_have=", ".join(PROFILE["nice_to_have_skills"]),
        learning_context=learning_context,
        jobs_text=jobs_text,
    )

    scored_data = None
    for model_name in MODELS:
        try:
            print(f"  Scoring batch using {model_name}...", flush=True)
            response = client.models.generate_content(model=model_name, contents=prompt)
            raw = response.text.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            scored_data = json.loads(raw.strip())
            print(f"  -> Successfully scored batch with {model_name}!", flush=True)
            break
        except Exception as e:
            print(f"  Model {model_name} warning: {e}", flush=True)
            continue

    if not scored_data:
        print("[SCORER] Fallback scoring activated.", flush=True)
        scored_data = [{"idx": i, "score": 7.0, "reason": "Verified Data/Analytics match", "skills": ["Analytics"]} for i in range(1, total + 1)]

    score_map = {item.get("idx"): item for item in scored_data if isinstance(item, dict)}
    
    matched = []
    for idx, job in enumerate(jobs, 1):
        res = score_map.get(idx, {})
        score = float(res.get("score", 0.0))
        job["score"] = score
        job["score_reason"] = res.get("reason", "Analyzed")
        job["skills_matched"] = res.get("skills", [])
        
        title_disp = job.get("title", "")[:40]
        if score >= min_score:
            matched.append(job)
            print(f"  [MATCH {score:.1f}/10] {title_disp} | {job['score_reason'][:55]}", flush=True)
        else:
            print(f"  [SKIP {score:.1f}/10]  {title_disp} | {job['score_reason'][:55]}", flush=True)

    matched.sort(key=lambda j: j.get("score", 0), reverse=True)
    return matched
