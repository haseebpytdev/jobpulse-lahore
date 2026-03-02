"""
Adapter: LinkedIn Jobs — stub.

Uncomment and register when scrape_linkedin_jobs is implemented (browser/API).
"""
from __future__ import annotations

from app.models import JobIn
from app.scrapers.base import Scraper, filter_jobs
from app.scrapers.linkedin_jobs import scrape_linkedin_jobs


class LinkedInJobsScraper:
    name = "linkedin_jobs"

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        jobs = scrape_linkedin_jobs(query=query, location=location, limit=limit)
        return filter_jobs(jobs, query=query, location=location, limit=limit)
