"""
Scraper interface and base for the multi-source engine.

All sources implement fetch(query, location, limit) and return list[JobIn].
Shared post-fetch filtering by query/location happens in filter_jobs().
"""
from __future__ import annotations

from typing import Protocol

from app.models import JobIn


def filter_jobs(
    jobs: list[JobIn],
    *,
    query: str = "",
    location: str = "",
    limit: int = 50,
) -> list[JobIn]:
    """
    Filter fetched jobs by query (title/company) and location (remote/lahore).
    Returns up to `limit` jobs. Use after fetch when the source does not support params.
    """
    q = (query or "").strip().lower()
    loc = (location or "").strip().lower()

    if not q and not loc:
        return jobs[:limit]

    out: list[JobIn] = []
    for job in jobs:
        if q:
            title = (job.get("title") or "").lower()
            company = (job.get("company") or "").lower()
            if q not in title and q not in company:
                continue
        if loc == "remote":
            if "remote" not in (job.get("location") or "").lower():
                continue
        elif loc == "lahore":
            if "lahore" not in (job.get("location") or "").lower():
                continue
        out.append(job)
        if len(out) >= limit:
            break
    return out


class Scraper(Protocol):
    """Protocol for a job source scraper."""

    name: str

    def fetch(
        self,
        *,
        query: str = "",
        location: str = "",
        limit: int = 50,
    ) -> list[JobIn]:
        """Fetch jobs from this source. Returns normalized JobIn list."""
        ...
