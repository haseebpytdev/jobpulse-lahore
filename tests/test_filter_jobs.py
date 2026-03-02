"""Tests for filter_jobs (query/location post-fetch filtering)."""
import pytest

from app.scrapers.base import filter_jobs

SAMPLE_JOBS = [
    {"title": "Python Developer", "company": "Acme", "location": "Remote", "source": "ro", "role_type": "full", "posted_date_text": "today", "apply_url": "https://a.com/1"},
    {"title": "Django Backend", "company": "Python Co", "location": "Lahore", "source": "ro", "role_type": "intern", "posted_date_text": "today", "apply_url": "https://a.com/2"},
    {"title": "Java Engineer", "company": "Other", "location": "Remote", "source": "ro", "role_type": "full", "posted_date_text": "today", "apply_url": "https://a.com/3"},
]


def test_filter_jobs_empty_query_and_location_returns_slice():
    result = filter_jobs(SAMPLE_JOBS, query="", location="", limit=2)
    assert len(result) == 2
    assert result[0]["title"] == "Python Developer"


def test_filter_jobs_query_matches_title():
    result = filter_jobs(SAMPLE_JOBS, query="python", location="", limit=10)
    assert len(result) >= 1
    assert any("python" in (j.get("title") or "").lower() for j in result)


def test_filter_jobs_query_matches_company():
    result = filter_jobs(SAMPLE_JOBS, query="python", location="", limit=10)
    assert len(result) >= 1
    assert any("python" in (j.get("company") or "").lower() for j in result)


def test_filter_jobs_location_remote():
    result = filter_jobs(SAMPLE_JOBS, query="", location="remote", limit=10)
    assert len(result) == 2
    assert all("remote" in (j.get("location") or "").lower() for j in result)


def test_filter_jobs_location_lahore():
    result = filter_jobs(SAMPLE_JOBS, query="", location="lahore", limit=10)
    assert len(result) == 1
    assert "lahore" in (result[0].get("location") or "").lower()


def test_filter_jobs_query_and_location_combined():
    result = filter_jobs(SAMPLE_JOBS, query="python", location="remote", limit=10)
    assert len(result) == 1
    assert result[0]["title"] == "Python Developer" and "remote" in (result[0].get("location") or "").lower()


def test_filter_jobs_respects_limit():
    result = filter_jobs(SAMPLE_JOBS, query="", location="", limit=1)
    assert len(result) == 1
