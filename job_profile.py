# -*- coding: utf-8 -*-
"""
job_profile.py - Sandeep Kaur's target profile and strict filtering criteria
"""
PROFILE = {
    "name": "Sandeep Kaur",
    "current_title": "BI Developer and Analytics Engineer",
    "years_experience": 3,
    "current_company": "IndiaMART InterMESH",
    "target_titles": [
        "BI Developer", "BI Engineer", "Analytics Engineer",
        "Senior Data Analyst", "Business Intelligence Analyst",
        "Reporting Engineer", "Dashboard Developer",
        "Data Engineer", "BI Analyst", "Revenue Operations Analyst"
    ],
    "must_have_skills": [
        "Power BI", "DAX", "SQL", "BigQuery", "Redshift",
        "semantic modelling", "data marts", "anomaly detection"
    ],
    "nice_to_have_skills": [
        "Python", "pandas", "TypeScript", "Next.js", "React",
        "statistical analysis", "LLM workflows", "FastAPI",
        "Power Automate", "AWS", "dbt", "Looker"
    ],
    "experience_level": "mid",  # 2-5 years (reject 5+ mandatory)
    "location_criteria": {
        "candidate_country": "India",
        "allowed_geos": [
            "Worldwide", "Global", "Anywhere", "APAC", "Work from Anywhere",
            "India", "India Remote", "India Hybrid",
            "Dubai", "UAE", "Abu Dhabi" # Visa relocation friendly
        ],
        "disallowed_domestic_remotes": [
            "USA Only", "US Only", "United States", "North America",
            "UK Only", "United Kingdom", "Canada Only", "Australia Only",
            "Europe Only", "EU Only", "Germany Only", "LATAM"
        ]
    },
    "employment_type": {
        "require_full_time": True,
        "strictly_exclude": ["contract", "contractor", "freelance", "temporary", "temp", "part-time"]
    },
    "filters": {
        "min_experience_required": 5,
        "max_job_age_days": 7,
        "min_relevance_score": 7.0
    },
    "resume_summary": """
BI developer and analytics engineer with 3+ years at IndiaMART (India's largest B2B marketplace).
Builds Power BI models, custom Next.js dashboards, cloud warehouse data marts (BigQuery, Redshift),
and automated reporting. Designed company-wide Ads Anomaly RCA platform using statistical methods
(log-log regression, Holt-Winters, 3-sigma MAD bands). Cut report refresh from 2 hrs to 10 mins.
Automated KPI reporting saving 3-4 hrs/week. Mentored junior analysts. 4 company awards.
""".strip()
}
