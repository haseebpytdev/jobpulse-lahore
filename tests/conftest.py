"""Shared pytest fixtures."""
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
