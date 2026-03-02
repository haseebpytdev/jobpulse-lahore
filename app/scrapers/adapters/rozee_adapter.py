"""
Adapter: Rozee.pk → Scraper protocol.
"""
from __future__ import annotations

from app.models import JobIn
from app.scrapers.base import Scraper, filter_jobs
from app.scrapers.rozee import scrape_rozee_python_lahore


class RozeeScraper:
    name = "rozee"

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        jobs = scrape_rozee_python_lahore(max_pages=1, delay_sec=1.0)
        return filter_jobs(jobs, query=query, location=location, limit=limit)
