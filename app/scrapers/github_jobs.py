"""
GitHub Jobs scraper.

NOTE: The official GitHub Jobs API (jobs.github.com/positions.json) was deprecated
and shut down. This module tries the legacy endpoint first; if it fails, you can
point JOBS_JSON_URL to a community repo or any JSON array of job objects with
keys like title, company, url, etc.
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

# Legacy API (may 404/410); replace with a repo raw URL if needed
LEGACY_API_URL = "https://jobs.github.com/positions.json"
# Example fallback: a repo that hosts jobs.json (update to a real one if you have it)
JOBS_JSON_URL = "https://raw.githubusercontent.com/remote-jobs-com/remote-jobs/main/jobs.json"
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobPulse/1.0)"}


def scrape_github_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch job listings from GitHub Jobs–style JSON (legacy API or repo).
    Returns list of dicts matching jobs table schema; source="github_jobs".
    """
    out: List[Dict[str, Any]] = []

    # Try legacy API first (description=python)
    try:
        resp = requests.get(
            LEGACY_API_URL,
            params={"description": "python", "location": ""},
            headers=DEFAULT_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        data = []

    if isinstance(data, list):
        for j in data:
            if not isinstance(j, dict):
                continue
            title = (j.get("title") or j.get("position") or "").strip()
            company = (j.get("company") or j.get("company_name") or "Unknown").strip()
            apply_url = (j.get("url") or j.get("link") or "").strip()
            if not title or not apply_url:
                continue
            location = (j.get("location") or "Remote").strip()
            lt = title.lower()
            role_type = (
                "intern"
                if "intern" in lt
                else "trainee"
                if "trainee" in lt
                else "junior"
                if "junior" in lt
                else "entry"
            )
            out.append(
                {
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "github_jobs",
                    "role_type": role_type,
                    "posted_date_text": str(j.get("date") or j.get("created_at") or "unknown"),
                    "posted_at": None,
                    "apply_url": apply_url,
                }
            )
            if len(out) >= limit:
                return out

    return out
