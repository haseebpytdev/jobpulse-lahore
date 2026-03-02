"""
Wellfound (AngelList Talent) scraper — startup jobs.

Search URL: wellfound.com/jobs. No public API; HTML scraping. Filter via filter_jobs().
"""
from __future__ import annotations

import time
import urllib.parse
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://wellfound.com"
JOBS_URL = "https://wellfound.com/jobs"

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


def scrape_wellfound(
    query: str = "",
    location: str = "",
    limit: int = 50,
    max_pages: int = 2,
    delay_sec: float = 1.5,
) -> List[Dict[str, Any]]:
    """
    Scrape Wellfound job listings. Site may use JS; if fetched=0 try Playwright.
    """
    results: List[Dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    for page in range(1, max_pages + 1):
        params: Dict[str, str] = {}
        if query:
            params["query"] = query.strip()
        if location:
            params["locations[]"] = location.strip()
        if page > 1:
            params["page"] = str(page)

        url = JOBS_URL + ("?" + urllib.parse.urlencode(params) if params else "")
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = (
            soup.select("[data-testid='job-card'], .job-card, .JobCard")
            or soup.select("a[href*='/jobs/']")
            or soup.select("[class*='JobCard']")
        )

        for card in cards:
            link_el = card if card.name == "a" else card.select_one("a[href*='/jobs/'], a")
            if not link_el:
                continue
            href = (link_el.get("href") or "").strip()
            if href.startswith("/"):
                href = BASE_URL + href
            title_el = link_el.select_one("h2, h3, .title, [class*='title']") or link_el
            title = _clean(title_el.get_text())
            if not title or not href:
                continue

            company_el = card.select_one("[class*='company'], .CompanyLink, .company-name")
            company = _clean(company_el.get_text()) if company_el else "Unknown"
            loc_el = card.select_one("[class*='location'], .location")
            loc_text = _clean(loc_el.get_text()) if loc_el else "Remote"

            results.append(
                {
                    "title": title,
                    "company": company,
                    "location": loc_text,
                    "source": "wellfound",
                    "role_type": _infer_role_type(title),
                    "posted_date_text": "unknown",
                    "posted_at": None,
                    "apply_url": href,
                }
            )
            if len(results) >= limit * 2:
                break

        if len(results) >= limit * 2:
            break
        if page < max_pages:
            time.sleep(delay_sec)

    return results
