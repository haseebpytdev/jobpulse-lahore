"""
Rozee.pk scraper for Python / Lahore job listings.

Output dicts match the jobs table schema (without scraped_at; add at insert time).

NOTE — Cloudflare: Rozee may return "Access denied" (Error 1005) for plain
requests. To test or run in production, use Playwright (or similar) to drive
a real browser and pass the Cloudflare challenge, then parse the resulting HTML.
Example: pip install playwright && playwright install chromium;
use sync_playwright() and page.goto(BASE_URL), then page.content() for soup.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.rozee.pk/job/jsearch/q/python%20lahore"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def _clean(text: str) -> str:
    """Normalize whitespace and strip."""
    if not text:
        return ""
    return " ".join(text.split()).strip()


def _infer_role_type(title: str) -> str:
    """Infer role_type from title for DB compatibility."""
    t = title.lower()
    if "intern" in t:
        return "intern"
    if "trainee" in t:
        return "trainee"
    return "junior"


def scrape_rozee_python_lahore(
    max_pages: int = 1,
    delay_sec: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Scrape Rozee search results for Python jobs in Lahore.

    Returns a list of dicts matching the jobs table schema (title, company,
    location, source, role_type, posted_date_text, posted_at, apply_url).
    scraped_at is added when inserting into the DB.

    Args:
        max_pages: Number of result pages to fetch.
        delay_sec: Seconds to wait between requests to reduce blocking risk.
    """
    results: List[Dict[str, Any]] = []

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    for page in range(1, max_pages + 1):
        url = BASE_URL if page == 1 else f"{BASE_URL}/fp/{page}"

        resp = session.get(url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Temporary debug: confirm Rozee HTML is loaded
        print("PAGE TITLE:", soup.title.get_text() if soup.title else "No title")
        print("HTML LENGTH:", len(resp.text))

        # Rozee markup may change; adjust selectors if the site updates.
        job_cards = soup.select("li.job, div.job, .job, .job-listing, .job-list")

        if not job_cards:
            print("⚠️ No job cards found — HTML structure likely changed")

        for card in job_cards:
            # Temporary debug: show actual card structure
            print("CARD HTML:", str(card)[:200])

            title_el = card.select_one("a")
            company_el = card.select_one(".comp-name, .company")
            location_el = card.select_one(".location, .loc")
            date_el = card.select_one(".date, .posted, .job-date")

            if not title_el:
                continue

            title = _clean(title_el.get_text())
            apply_url = title_el.get("href") or ""
            if apply_url and apply_url.startswith("/"):
                apply_url = "https://www.rozee.pk" + apply_url

            if not apply_url:
                continue

            company = _clean(company_el.get_text()) if company_el else "Unknown"
            location = _clean(location_el.get_text()) if location_el else "Lahore"
            posted_date_text = _clean(date_el.get_text()) if date_el else "unknown"

            results.append(
                {
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": "rozee",
                    "role_type": _infer_role_type(title),
                    "posted_date_text": posted_date_text,
                    "posted_at": None,
                    "apply_url": apply_url,
                }
            )

        if page < max_pages:
            time.sleep(delay_sec)

    return results
