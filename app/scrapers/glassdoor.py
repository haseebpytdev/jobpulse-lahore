"""
Glassdoor scraper — good volume, often anti-bot.

Tries HTML search. If fetched=0, consider Playwright or official API.
Filter via filter_jobs().
"""
from __future__ import annotations

import time
import urllib.parse
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.glassdoor.com"
SEARCH_PATH = "/Job/jobs.htm"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}


def _clean(t: str) -> str:
    return " ".join((t or "").split()).strip()


def _infer_role_type(title: str) -> str:
    lt = title.lower()
    if "intern" in lt:
        return "intern"
    if "trainee" in lt:
        return "trainee"
    return "junior"


def scrape_glassdoor(
    query: str = "",
    location: str = "",
    limit: int = 50,
    max_pages: int = 2,
    delay_sec: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Scrape Glassdoor job search. Site may block plain requests; returns [] on failure.
    """
    results: List[Dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    for page in range(1, max_pages + 1):
        params: Dict[str, str] = {}
        if query:
            params["keyword"] = query.strip()
        if location:
            params["locT"] = "C"
            params["locKeyword"] = location.strip()
        if page > 1:
            params["p"] = str(page)

        url = BASE_URL + SEARCH_PATH + ("?" + urllib.parse.urlencode(params) if params else "")
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = (
            soup.select("[data-job-id], .job-card, .JobCard")
            or soup.select("li.react-job-listing")
            or soup.select("article[class*='job']")
        )

        for card in cards:
            link_el = card.select_one("a[href*='/job-listing'], a[href*='/Job/']")
            if not link_el:
                continue
            title = _clean(link_el.get_text())
            apply_url = (link_el.get("href") or "").strip()
            if apply_url.startswith("/"):
                apply_url = BASE_URL + apply_url
            if not title or not apply_url:
                continue

            company_el = card.select_one("[class*='company'], .employer")
            company = _clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.select_one("[class*='location'], .location")
            loc_text = _clean(loc_el.get_text()) if loc_el else ""

            results.append(
                {
                    "title": title,
                    "company": company,
                    "location": loc_text or "Unknown",
                    "source": "glassdoor",
                    "role_type": _infer_role_type(title),
                    "posted_date_text": "unknown",
                    "posted_at": None,
                    "apply_url": apply_url,
                }
            )
            if len(results) >= limit * 2:
                break

        if len(results) >= limit * 2:
            break
        if page < max_pages:
            time.sleep(delay_sec)

    return results
