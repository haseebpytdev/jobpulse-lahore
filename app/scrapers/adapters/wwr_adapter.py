"""
Adapter: We Work Remotely RSS → Scraper protocol.
"""
from __future__ import annotations

from app.models import JobIn
from app.scrapers.base import Scraper, filter_jobs
from app.scrapers.weworkremotely import scrape_weworkremotely


class WWRSSScraper:
    name = "wwr"

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        fetch_limit = min(limit * 3, 200) if (query or location) else limit
        jobs = scrape_weworkremotely(query=query, location=location, limit=fetch_limit)
        return filter_jobs(jobs, query=query, location=location, limit=limit)
