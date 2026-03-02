"""
Engine runner: runs scrapers with per-source isolation, timing, and metrics.

Returns a structured RunReport for the UI and logging.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from app.db import upsert_jobs
from app.scrapers.registry import SOURCE_DISPLAY_NAMES, SCRAPERS

logger = logging.getLogger(__name__)


@dataclass
class SourceResult:
    """Result of running one scraper source."""

    source_key: str
    display_name: str
    status: str  # "ok" | "error" | "disabled"
    fetched: int
    inserted: int
    updated: int
    duration_ms: int
    error_message: str = ""


@dataclass
class RunReport:
    """Full report after running the engine."""

    total_fetched: int = 0
    total_inserted: int = 0
    total_updated: int = 0
    results: list[SourceResult] = field(default_factory=list)

    @property
    def status_summary(self) -> str:
        parts = []
        for r in self.results:
            if r.status == "ok":
                parts.append(f"{r.display_name} ok")
            elif r.status == "disabled":
                parts.append(f"{r.display_name} disabled")
            else:
                short = (r.error_message or "error")[:40].replace(" ", "_")
                parts.append(f"{r.display_name} {short}")
        return ", ".join(parts)


def run_engine(
    sources: list[str] | None = None,
    query: str = "",
    location: str = "",
    limit: int = 50,
) -> RunReport:
    """
    Run selected scrapers, upsert results, capture per-source metrics.
    If sources is None or empty, run all registered scrapers.
    """
    report = RunReport()
    if not sources:
        sources = list(SCRAPERS.keys())

    for source_key in sources:
        scraper = SCRAPERS.get(source_key)
        display_name = SOURCE_DISPLAY_NAMES.get(source_key, source_key)

        if not scraper:
            report.results.append(
                SourceResult(
                    source_key=source_key,
                    display_name=display_name,
                    status="disabled",
                    fetched=0,
                    inserted=0,
                    updated=0,
                    duration_ms=0,
                    error_message="not in registry",
                )
            )
            continue

        start = time.perf_counter()
        try:
            jobs = scraper.fetch(query=query, location=location, limit=limit)
            inserted, updated = upsert_jobs(jobs)
            duration_ms = int((time.perf_counter() - start) * 1000)
            report.results.append(
                SourceResult(
                    source_key=source_key,
                    display_name=display_name,
                    status="ok",
                    fetched=len(jobs),
                    inserted=inserted,
                    updated=updated,
                    duration_ms=duration_ms,
                )
            )
            report.total_fetched += len(jobs)
            report.total_inserted += inserted
            report.total_updated += updated
            logger.info(
                "engine source=%s fetched=%s inserted=%s updated=%s duration_ms=%s",
                source_key,
                len(jobs),
                inserted,
                updated,
                duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            err_msg = str(e)[:200]
            report.results.append(
                SourceResult(
                    source_key=source_key,
                    display_name=display_name,
                    status="error",
                    fetched=0,
                    inserted=0,
                    updated=0,
                    duration_ms=duration_ms,
                    error_message=err_msg,
                )
            )
            logger.warning(
                "engine source=%s error=%s duration_ms=%s",
                source_key,
                err_msg,
                duration_ms,
            )

    return report
