"""
Scraper registry: toggle sources on/off without touching /refresh.

Keys are used in URLs (sources=remoteok,wwr). Display names for UI.
"""
from __future__ import annotations

from typing import Dict

from app.scrapers.adapters.github_jobs_adapter import GitHubJobsScraper
from app.scrapers.adapters.glassdoor_adapter import GlassdoorScraper
from app.scrapers.adapters.indeed_adapter import IndeedScraper
from app.scrapers.adapters.linkedin_jobs_adapter import LinkedInJobsScraper
from app.scrapers.adapters.mustakbil_adapter import MustakbilScraper
from app.scrapers.adapters.remoteok_adapter import RemoteOKScraper
from app.scrapers.adapters.rozee_adapter import RozeeScraper
from app.scrapers.adapters.wellfound_adapter import WellfoundScraper
from app.scrapers.adapters.wwr_adapter import WWRSSScraper
from app.scrapers.base import Scraper

SCRAPERS: Dict[str, Scraper] = {
    "remoteok": RemoteOKScraper(),
    "weworkremotely": WWRSSScraper(),
    "rozee": RozeeScraper(),
    "github_jobs": GitHubJobsScraper(),
    "mustakbil": MustakbilScraper(),
    "glassdoor": GlassdoorScraper(),
    "wellfound": WellfoundScraper(),
    "indeed": IndeedScraper(),
    "linkedin_jobs": LinkedInJobsScraper(),
}

SOURCE_DISPLAY_NAMES: Dict[str, str] = {
    "remoteok": "RemoteOK",
    "weworkremotely": "WWR",
    "rozee": "Rozee",
    "github_jobs": "GitHub Jobs",
    "mustakbil": "Mustakbil",
    "glassdoor": "Glassdoor",
    "wellfound": "Wellfound",
    "indeed": "Indeed",
    "linkedin_jobs": "LinkedIn Jobs",
}
