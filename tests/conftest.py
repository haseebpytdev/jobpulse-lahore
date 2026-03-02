"""Shared pytest fixtures.

Uses in-memory SQLite to avoid Windows file-lock teardown errors (temp files
staying open). Engine/upsert tests get an isolated DB per run.
"""
import pytest

from app import db as db_module


@pytest.fixture
def temp_db(monkeypatch):
    """Use an in-memory SQLite DB for tests (no file to lock on Windows)."""
    uri = "file:jobpulse_test?mode=memory&cache=shared"
    monkeypatch.setattr(db_module, "DB_PATH", uri)

    def get_conn_uri():
        import sqlite3
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(db_module, "get_conn", get_conn_uri)
    db_module.init_db()
    yield uri
