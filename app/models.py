"""
Canonical job schema for the multi-source scraper engine.

All scrapers output JobIn; the engine upserts into the DB.
"""
from __future__ import annotations

from typing import Optional, TypedDict


class JobIn(TypedDict, total=False):
    """Scraped job input — all sources output these fields."""

    title: str
    company: str
    location: str
    source: str
    role_type: str
    posted_date_text: str
    posted_at: Optional[str]
    apply_url: str
    # Optional
    source_job_id: Optional[str]
    tags: Optional[list[str]]
    salary_text: Optional[str]
