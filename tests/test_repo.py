"""Tests for repo list_jobs and count_jobs (filters and freshness)."""
import pytest

from app.repo import list_jobs, count_jobs


@pytest.fixture
def temp_db_with_jobs(monkeypatch):
    """In-memory DB with a few jobs for repo tests."""
    from contextlib import contextmanager
    import sqlite3

    from app import db as db_module
    from app import repo as repo_module

    uri = "file:jobpulse_repo_test?mode=memory&cache=shared"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    @contextmanager
    def db_conn_memory():
        try:
            yield conn
            conn.commit()
        finally:
            pass

    monkeypatch.setattr(db_module, "DB_PATH", uri)
    monkeypatch.setattr(db_module, "db_conn", db_conn_memory)
    monkeypatch.setattr(repo_module, "db_conn", db_conn_memory)
    db_module.init_db()

    with db_conn_memory() as c:
        cur = c.cursor()
        cur.execute(
            """INSERT INTO jobs (title, company, location, source, role_type, posted_date_text,
               posted_at, apply_url, scraped_at, first_seen_at, last_seen_at, is_active)
               VALUES ('Job A', 'Co A', 'Lahore', 'rozee', 'intern', 'today', NULL, 'https://a.com/1',
                       datetime('now'), datetime('now'), datetime('now'), 1)"""
        )
        cur.execute(
            """INSERT INTO jobs (title, company, location, source, role_type, posted_date_text,
               posted_at, apply_url, scraped_at, first_seen_at, last_seen_at, is_active)
               VALUES ('Job B', 'Co B', 'Remote', 'remoteok', 'junior', 'yesterday', NULL, 'https://a.com/2',
                       datetime('now'), datetime('now'), datetime('now'), 1)"""
        )
        cur.execute(
            """INSERT INTO jobs (title, company, location, source, role_type, posted_date_text,
               posted_at, apply_url, scraped_at, first_seen_at, last_seen_at, is_active)
               VALUES ('Job C', 'Co C', 'Lahore', 'mustakbil', 'trainee', 'old', NULL, 'https://a.com/3',
                       datetime('now', '-5 days'), datetime('now', '-5 days'), datetime('now', '-5 days'), 1)"""
        )
    conn.commit()

    try:
        yield uri
    finally:
        conn.close()


def test_list_jobs_returns_all_without_freshness(temp_db_with_jobs):
    jobs = list_jobs(limit=10, freshness="")
    assert len(jobs) == 3
    titles = {j["title"] for j in jobs}
    assert "Job A" in titles and "Job B" in titles and "Job C" in titles


def test_list_jobs_new_today_filters_by_first_seen(temp_db_with_jobs):
    jobs = list_jobs(limit=10, freshness="new_today")
    assert len(jobs) == 2
    titles = {j["title"] for j in jobs}
    assert "Job A" in titles and "Job B" in titles
    assert "Job C" not in titles


def test_list_jobs_last_3_days_includes_older(temp_db_with_jobs):
    jobs = list_jobs(limit=10, freshness="last_3_days")
    assert len(jobs) >= 2


def test_count_jobs_matches_list_jobs(temp_db_with_jobs):
    total = count_jobs(freshness="")
    assert total == 3
    total_new = count_jobs(freshness="new_today")
    assert total_new == 2


def test_list_jobs_respects_q_and_source(temp_db_with_jobs):
    jobs = list_jobs(q="A", limit=10)
    assert len(jobs) >= 1
    assert any("A" in (j.get("title") or "") or "A" in (j.get("company") or "") for j in jobs)
    jobs_rozee = list_jobs(source="rozee", limit=10)
    assert len(jobs_rozee) == 1
    assert jobs_rozee[0]["source"] == "rozee"
