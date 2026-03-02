"""
Adapter: Wellfound (AngelList) → Scraper protocol.
"""
from __future__ import annotations

from app.models import JobIn
from app.scrapers.base import Scraper, filter_jobs
from app.scrapers.wellfound import scrape_wellfound


class WellfoundScraper:
    name = "wellfound"

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        jobs = scrape_wellfound(
            query=query,
            location=location,
            limit=limit,
            max_pages=2,
            delay_sec=1.5,
        )
        return filter_jobs(jobs, query=query, location=location, limit=limit)
