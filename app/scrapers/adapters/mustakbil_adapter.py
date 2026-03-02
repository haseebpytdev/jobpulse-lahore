"""
Adapter: Mustakbil (Pakistan) → Scraper protocol.
"""
from __future__ import annotations

from app.models import JobIn
from app.scrapers.base import Scraper, filter_jobs
from app.scrapers.mustakbil import scrape_mustakbil


class MustakbilScraper:
    name = "mustakbil"

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        jobs = scrape_mustakbil(
            query=query,
            location=location,
            limit=limit,
            max_pages=3,
            delay_sec=1.0,
        )
        return filter_jobs(jobs, query=query, location=location, limit=limit)
