"""
RemoteOK scraper — fetches jobs from the public JSON API.

No HTML parsing; stable and not blocked by Cloudflare.
Output dicts match the jobs table schema (without scraped_at).
"""
from __future__ import annotations

from typing import Any, Dict, List

import requests

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def scrape_remoteok_python(limit: int = 30) -> List[Dict[str, Any]]:
    """
    RemoteOK provides a JSON endpoint.
    Stable ingestion, no HTML parsing brittleness.
    """
    url = "https://remoteok.com/api"
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    # First element is metadata; the rest are jobs
    jobs = [j for j in data[1:] if isinstance(j, dict)]

    out: List[Dict[str, Any]] = []
    for j in jobs:
        title = (j.get("position") or "").strip()
        company = (j.get("company") or "Unknown").strip()
        apply_url = (j.get("url") or "").strip()
        tags = [t.lower() for t in (j.get("tags") or [])]

        if not title or not apply_url:
            continue

        # Filter to Python-ish
        if "python" not in title.lower() and "python" not in tags:
            continue

        # Role type heuristic
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
                "location": "Remote",
                "source": "remoteok",
                "role_type": role_type,
                "posted_date_text": str(j.get("date") or "unknown"),
                "posted_at": None,
                "apply_url": apply_url,
            }
        )

        if len(out) >= limit:
            break

    return out
