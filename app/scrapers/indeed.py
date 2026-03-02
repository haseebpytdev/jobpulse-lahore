"""
Indeed scraper — stub. Indeed blocks plain HTTP; needs browser (Playwright) or official API.

Enable when you have Playwright or Indeed API key. Returns [] for now.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def scrape_indeed(
    query: str = "",
    location: str = "",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Stub: Indeed requires browser or API. Returns [] until Playwright/API is integrated.
    """
    logger.info("Indeed scraper is a stub (needs browser/API); returning no jobs.")
    return []
