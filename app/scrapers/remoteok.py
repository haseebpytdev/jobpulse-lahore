"""
RemoteOK scraper — fetches jobs from the public JSON API.

No HTML parsing; stable and not blocked by Cloudflare.
Hardened: shorter timeout, retry with backoff, returns [] on failure (SSL/network).
Output dicts match the jobs table schema (without scraped_at).
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

REMOTEOK_TIMEOUT = 10
REMOTEOK_RETRIES = 3
REMOTEOK_BACKOFF = [1, 2, 4]  # seconds before each retry


def scrape_remoteok(
    query: str = "",
    location: str = "",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch jobs from RemoteOK JSON API. No server-side search; returns all and caller
    should filter by query/location (e.g. via filter_jobs). Uses 10s timeout, retries with backoff.
    """
    url = "https://remoteok.com/api"
    last_error: Exception | None = None

    for attempt in range(REMOTEOK_RETRIES):
        try:
            resp = requests.get(
                url, headers=DEFAULT_HEADERS, timeout=REMOTEOK_TIMEOUT
            )
            resp.raise_for_status()
            break
        except requests.RequestException as e:
            last_error = e
            logger.warning(
                "RemoteOK attempt %s/%s failed: %s",
                attempt + 1,
                REMOTEOK_RETRIES,
                e,
            )
            if attempt < REMOTEOK_RETRIES - 1:
                time.sleep(REMOTEOK_BACKOFF[attempt])
    else:
        logger.error("RemoteOK all attempts failed: %s", last_error)
        return []

    data = resp.json()
    jobs = [j for j in data[1:] if isinstance(j, dict)]

    out: List[Dict[str, Any]] = []
    for j in jobs:
        title = (j.get("position") or "").strip()
        company = (j.get("company") or "Unknown").strip()
        apply_url = (j.get("url") or "").strip()
        tags = [t.lower() for t in (j.get("tags") or [])]

        if not title or not apply_url:
            continue

        # No hardcoded "python" filter — filter_jobs() applies query/location
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
        if len(out) >= limit * 3:
            break

    return out
