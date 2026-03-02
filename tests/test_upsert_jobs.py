"""Tests for upsert_jobs: inserted vs updated counting."""
import tempfile
from pathlib import Path

import pytest

from app import db as db_module


@pytest.fixture
def temp_db(monkeypatch):
    """Use a temporary SQLite file for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "jobs.db"
        monkeypatch.setattr(db_module, "DB_PATH", path)
        db_module.init_db()
        yield path
    # teardown: tmp dir removed


def test_upsert_jobs_empty_returns_zero():
    inserted, updated = db_module.upsert_jobs([])
    assert inserted == 0
    assert updated == 0


def test_upsert_jobs_first_run_inserts(temp_db):
    jobs = [
        {
            "title": "Test Job",
            "company": "Test Co",
            "location": "Remote",
            "source": "test",
            "role_type": "full",
            "posted_date_text": "today",
            "apply_url": "https://example.com/job1",
        }
    ]
    inserted, updated = db_module.upsert_jobs(jobs)
    assert inserted == 1
    assert updated == 0


def test_upsert_jobs_second_run_updates(temp_db):
    jobs = [
        {
            "title": "Test Job",
            "company": "Test Co",
            "location": "Remote",
            "source": "test",
            "role_type": "full",
            "posted_date_text": "today",
            "apply_url": "https://example.com/job1",
        }
    ]
    db_module.upsert_jobs(jobs)
    inserted, updated = db_module.upsert_jobs(jobs)
    assert inserted == 0
    assert updated == 1


def test_upsert_jobs_mixed_new_and_existing(temp_db):
    jobs1 = [
        {"title": "A", "company": "C", "location": "L", "source": "s", "role_type": "r", "posted_date_text": "d", "apply_url": "https://e.com/1"},
    ]
    inserted1, updated1 = db_module.upsert_jobs(jobs1)
    assert inserted1 == 1 and updated1 == 0

    jobs2 = [
        {"title": "A", "company": "C", "location": "L", "source": "s", "role_type": "r", "posted_date_text": "d", "apply_url": "https://e.com/1"},
        {"title": "B", "company": "C", "location": "L", "source": "s", "role_type": "r", "posted_date_text": "d", "apply_url": "https://e.com/2"},
    ]
    inserted2, updated2 = db_module.upsert_jobs(jobs2)
    assert inserted2 == 1
    assert updated2 == 1
