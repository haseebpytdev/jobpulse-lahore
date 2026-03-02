"""Shared pytest fixtures.

Patches db_conn to use in-memory SQLite so no file is locked on Windows teardown.
"""
import pytest

from app import db as db_module


@pytest.fixture
def temp_db(monkeypatch):
    """Use a shared in-memory SQLite DB for tests (no file to lock on Windows)."""
    from contextlib import contextmanager
    import sqlite3

    uri = "file:jobpulse_test?mode=memory&cache=shared"

    # Single shared connection that stays open for the whole test.
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    @contextmanager
    def db_conn_memory():
        try:
            yield conn
            conn.commit()
        finally:
            # Do not close here; the fixture will close after tests so the
            # shared in-memory DB (and its schema) stays alive.
            pass

    monkeypatch.setattr(db_module, "DB_PATH", uri)
    monkeypatch.setattr(db_module, "db_conn", db_conn_memory)

    # Initialize schema inside the same shared connection.
    db_module.init_db()

    try:
        yield uri
    finally:
        conn.close()
