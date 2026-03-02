"""
Rozee.pk scraper — dynamic query/location, multi-page.

Builds search URL from query/location; fetches up to max_pages (default 3).
Output dicts match the jobs table schema (without scraped_at).

NOTE — Cloudflare: Rozee may return "Access denied" for plain requests.
Use Playwright for production if needed.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

BASE_SEARCH = "https://www.rozee.pk/job/jsearch"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _clean(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()


def _infer_role_type(title: str) -> str:
    t = title.lower()
    if "intern" in t:
        return "intern"
    if "trainee" in t:
        return "trainee"
    return "junior"


def _build_search_url(query: str, location: str, page: int = 1) -> str:
    """Build Rozee search URL. e.g. q=python+lahore, page 2 = /fp/2."""
    parts = []
    if query:
        parts.append(query.strip().lower().replace(" ", "%20"))
    if location:
        parts.append(location.strip().lower().replace(" ", "%20"))
    q = "%20".join(parts) if parts else "python%20lahore"
    if page <= 1:
        return f"{BASE_SEARCH}/q/{q}"
    return f"{BASE_SEARCH}/q/{q}/fp/{page}"


def scrape_rozee(
    query: str = "",
    location: str = "",
    limit: int = 50,
    max_pages: int = 3,
    delay_sec: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Scrape Rozee search results. Fetches pages 1..max_pages, extracts job cards.
    Filter by query/location after fetch via filter_jobs().
    """
    results: List[Dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    for page in range(1, max_pages + 1):
        url = _build_search_url(query, location, page)
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
        except requests.RequestException:
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Card containers: prefer exact div.job
        job_cards = (
            soup.select("div.job")
            or soup.select("li.job")
            or soup.select("[class*='job-card']")
            or soup.select(".job-listing .item, .job-list > div, .job-list > li")
        )

        for card in job_cards:
            # Title + apply link: prefer link with /job/ in href
            link_el = (
                card.select_one("a.job-title, .job-title a, a[href*='/job/']")
                or card.select_one("h2 a, h3 a, .title a, .title")
                or card.select_one("a[href*='job']")
                or card.select_one("a")
            )
            if not link_el:
                continue

            title = _clean(link_el.get_text())
            apply_url = (link_el.get("href") or "").strip()
            if apply_url.startswith("/"):
                apply_url = "https://www.rozee.pk" + apply_url
            if not title or not apply_url:
                continue

            company_el = (
                card.select_one(".company-name, .comp-name, .company, .employer, [class*='company']")
                or card.select_one("a[href*='/company/']")
            )
            company = _clean(company_el.get_text()) if company_el else "Unknown"

            location_el = card.select_one(".location, .loc, .job-location, [class*='location']")
            location_text = _clean(location_el.get_text()) if location_el else "Lahore"

            date_el = card.select_one(".date, .posted, .job-date, .time, [class*='date']")
            posted_date_text = _clean(date_el.get_text()) if date_el else "unknown"

            results.append(
                {
                    "title": title,
                    "company": company,
                    "location": location_text,
                    "source": "rozee",
                    "role_type": _infer_role_type(title),
                    "posted_date_text": posted_date_text,
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
