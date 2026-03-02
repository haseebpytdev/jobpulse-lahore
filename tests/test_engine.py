"""Tests for run_engine with mocked scrapers."""
import pytest

from app.engine import run_engine, RunReport, SourceResult


class MockScraper:
    def __init__(self, name: str, jobs: list):
        self.name = name
        self.jobs = jobs

    def fetch(self, *, query: str = "", location: str = "", limit: int = 50):
        return self.jobs[:limit]


def test_run_engine_unknown_source_returns_disabled(temp_db):
    """Run with a source not in registry -> status disabled."""
    report = run_engine(sources=["nonexistent"])
    assert len(report.results) == 1
    assert report.results[0].status == "disabled"
    assert report.results[0].display_name == "nonexistent"


def test_run_engine_with_mock_scraper(monkeypatch, temp_db):
    from app.scrapers import registry as reg
    jobs = [
        {"title": "T", "company": "C", "location": "L", "source": "mock", "role_type": "r", "posted_date_text": "d", "apply_url": "https://x.com/1"},
    ]
    monkeypatch.setattr(reg, "SCRAPERS", {"mock": MockScraper("mock", jobs)})
    monkeypatch.setattr(reg, "SOURCE_DISPLAY_NAMES", {"mock": "Mock"})
    report = run_engine(sources=["mock"], limit=50)
    assert report.total_fetched == 1
    assert report.total_inserted == 1
    assert len(report.results) == 1
    assert report.results[0].status == "ok"
    assert report.results[0].fetched == 1
    assert report.results[0].inserted == 1


def test_run_engine_status_summary(temp_db):
    report = run_engine(sources=["nonexistent"])
    assert "nonexistent" in report.status_summary
    assert "disabled" in report.status_summary
