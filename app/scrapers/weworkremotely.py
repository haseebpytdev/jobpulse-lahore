"""
We Work Remotely scraper — fetches from the public RSS feed.

Stable; no Cloudflare. Output dicts match the jobs table schema (without scraped_at).
Feed: https://weworkremotely.com/categories/remote-programming-jobs.rss
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List

import requests

RSS_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobPulse/1.0)"}


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    return (el.text or "").strip()


def scrape_weworkremotely(
    query: str = "",
    location: str = "",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Fetch We Work Remotely programming jobs from RSS.
    No server-side search; returns all and caller filters by query/location (e.g. filter_jobs).
    """
    resp = requests.get(RSS_URL, headers=DEFAULT_HEADERS, timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    channel = root.find("channel")
    if channel is None:
        return []

    out: List[Dict[str, Any]] = []
    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")

        title = _text(title_el)
        apply_url = _text(link_el)
        if not title or not apply_url:
            continue

        company = "Unknown"
        if " at " in title:
            parts = title.split(" at ", 1)
            if len(parts) == 2:
                company = parts[1].strip()
                title = parts[0].strip()
        elif " - " in title:
            parts = title.split(" - ", 1)
            if len(parts) == 2:
                company = parts[0].strip()
                title = parts[1].strip()

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
                "source": "weworkremotely",
                "role_type": role_type,
                "posted_date_text": _text(pub_el) or "unknown",
                "posted_at": None,
                "apply_url": apply_url,
            }
        )
        if len(out) >= limit * 3:
            break

    return out
