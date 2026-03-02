"""
LinkedIn Jobs scraper — stub. LinkedIn is heavily anti-bot; needs browser or official API.

Enable when you have Playwright or LinkedIn API. Returns [] for now.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def scrape_linkedin_jobs(
    query: str = "",
    location: str = "",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Stub: LinkedIn requires browser or official API. Returns [] until integrated.
    """
    logger.info("LinkedIn scraper is a stub (anti-bot); returning no jobs.")
    return []
