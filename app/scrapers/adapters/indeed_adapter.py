"""
Adapter: Indeed (Pakistan + Global) — stub.

Uncomment and register when scrape_indeed is implemented (Playwright/API).
"""
from __future__ import annotations

from app.models import JobIn
from app.scrapers.base import Scraper, filter_jobs
from app.scrapers.indeed import scrape_indeed


class IndeedScraper:
    name = "indeed"

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        jobs = scrape_indeed(query=query, location=location, limit=limit)
        return filter_jobs(jobs, query=query, location=location, limit=limit)
