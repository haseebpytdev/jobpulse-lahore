"""
Mustakbil.com (Pakistan) scraper — dynamic query/location, multi-page.

High-value Pakistan jobs. Fetches search results; filter via filter_jobs().
"""
from __future__ import annotations

import time
import urllib.parse
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mustakbil.com"
SEARCH_URL = "https://www.mustakbil.com/jobs/pakistan"

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


def scrape_mustakbil(
    query: str = "",
    location: str = "",
    limit: int = 50,
    max_pages: int = 3,
    delay_sec: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Scrape Mustakbil Pakistan job listings. Uses search when query/location provided.
    Returns raw list; filter via filter_jobs().
    """
    results: List[Dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    for page in range(1, max_pages + 1):
        params: Dict[str, str] = {}
        if query:
            params["q"] = query.strip()
        if location:
            params["location"] = location.strip()
        if page > 1:
            params["page"] = str(page)

        url = SEARCH_URL + ("?" + urllib.parse.urlencode(params) if params else "")
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = (
            soup.select("div.job-card, .job-item, .job-listing, [class*='job-card']")
            or soup.select("article.job, .jobs-list .item")
        )

        for card in cards:
            link_el = (
                card.select_one("a.job-title, .job-title a, a[href*='/job/']")
                or card.select_one("h2 a, h3 a, .title a")
                or card.select_one("a")
            )
            if not link_el:
                continue
            title = _clean(link_el.get_text())
            apply_url = (link_el.get("href") or "").strip()
            if apply_url.startswith("/"):
                apply_url = BASE_URL + apply_url
            if not title or not apply_url:
                continue

            company_el = card.select_one(".company, .employer, [class*='company']")
            company = _clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.select_one(".location, .city, [class*='location']")
            loc_text = _clean(loc_el.get_text()) if loc_el else "Pakistan"
            date_el = card.select_one(".date, .posted, [class*='date']")
            posted = _clean(date_el.get_text()) if date_el else "unknown"

            results.append(
                {
                    "title": title,
                    "company": company,
                    "location": loc_text,
                    "source": "mustakbil",
                    "role_type": _infer_role_type(title),
                    "posted_date_text": posted,
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
