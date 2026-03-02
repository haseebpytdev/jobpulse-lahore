import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

DB_PATH = Path("data") / "jobs.db"


def get_conn() -> sqlite3.Connection:
  """
  Return a SQLite connection with Row factory enabled.
  Keeps DB under data/jobs.db and ensures the folder exists.
  """
  DB_PATH.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def _migrate_add_seen_columns(cur: sqlite3.Cursor) -> None:
  """Add first_seen_at, last_seen_at, is_active if missing (existing DBs)."""
  cur.execute("PRAGMA table_info(jobs)")
  cols = {row[1] for row in cur.fetchall()}
  if "first_seen_at" not in cols:
    cur.execute("ALTER TABLE jobs ADD COLUMN first_seen_at TEXT")
  if "last_seen_at" not in cols:
    cur.execute("ALTER TABLE jobs ADD COLUMN last_seen_at TEXT")
  if "is_active" not in cols:
    cur.execute("ALTER TABLE jobs ADD COLUMN is_active INTEGER DEFAULT 1")


def init_db(sample_jobs: Optional[List[Mapping[str, Any]]] = None) -> None:
  """
  Initialize SQLite schema and optional seed data.

  - UNIQUE(apply_url) for dedupe; first_seen_at / last_seen_at for freshness.
  - Migration adds first_seen_at, last_seen_at, is_active to existing DBs.
  """
  with get_conn() as conn:
    cur = conn.cursor()

    cur.execute(
      """
      CREATE TABLE IF NOT EXISTS jobs (
          id               INTEGER PRIMARY KEY AUTOINCREMENT,
          title            TEXT NOT NULL,
          company          TEXT NOT NULL,
          location         TEXT NOT NULL,
          source           TEXT NOT NULL,
          role_type        TEXT NOT NULL,
          posted_date_text TEXT NOT NULL,
          posted_at        DATE NULL,
          apply_url        TEXT NOT NULL UNIQUE,
          scraped_at       TEXT NOT NULL,
          first_seen_at    TEXT NULL,
          last_seen_at     TEXT NULL,
          is_active        INTEGER DEFAULT 1
      );
      """
    )

    _migrate_add_seen_columns(cur)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);")
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_jobs_role_type ON jobs(role_type);"
    )
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at);"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_last_seen_at ON jobs(last_seen_at);")

    if sample_jobs:
      now = datetime.now(timezone.utc).isoformat(timespec="seconds")
      payload: List[Dict[str, Any]] = []
      for job in sample_jobs:
        payload.append(
          {
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "source": job["source"],
            "role_type": job["role_type"],
            "posted_date_text": job.get("posted_date", ""),
            "posted_at": None,
            "apply_url": job["apply_url"],
            "scraped_at": now,
            "first_seen_at": now,
            "last_seen_at": now,
            "is_active": 1,
          }
        )

      cur.executemany(
        """
        INSERT OR IGNORE INTO jobs (
            title,
            company,
            location,
            source,
            role_type,
            posted_date_text,
            posted_at,
            apply_url,
            scraped_at,
            first_seen_at,
            last_seen_at,
            is_active
        )
        VALUES (
            :title,
            :company,
            :location,
            :source,
            :role_type,
            :posted_date_text,
            :posted_at,
            :apply_url,
            :scraped_at,
            :first_seen_at,
            :last_seen_at,
            :is_active
        );
        """,
        payload,
      )


def insert_jobs(jobs: List[Mapping[str, Any]]) -> int:
  """
  Insert scraped jobs into the DB. Adds scraped_at; UNIQUE(apply_url) skips duplicates.
  Returns the number of rows actually inserted.
  """
  if not jobs:
    return 0
  now = datetime.now(timezone.utc).isoformat(timespec="seconds")
  payload: List[Dict[str, Any]] = []
  for job in jobs:
    payload.append(
      {
        "title": job["title"],
        "company": job["company"],
        "location": job["location"],
        "source": job["source"],
        "role_type": job["role_type"],
        "posted_date_text": job.get("posted_date_text") or job.get("posted_date", ""),
        "posted_at": job.get("posted_at"),
        "apply_url": job["apply_url"],
        "scraped_at": now,
        "first_seen_at": now,
        "last_seen_at": now,
        "is_active": 1,
      }
    )
  inserted = 0
  with get_conn() as conn:
    cur = conn.cursor()
    for row in payload:
      cur.execute(
        """
        INSERT OR IGNORE INTO jobs (
            title, company, location, source, role_type,
            posted_date_text, posted_at, apply_url, scraped_at,
            first_seen_at, last_seen_at, is_active
        )
        VALUES (
            :title, :company, :location, :source, :role_type,
            :posted_date_text, :posted_at, :apply_url, :scraped_at,
            :first_seen_at, :last_seen_at, :is_active
        );
        """,
        row,
      )
      inserted += cur.rowcount
  return inserted


def upsert_jobs(jobs: List[Mapping[str, Any]]) -> tuple[int, int]:
  """
  Insert new jobs or update existing by apply_url.
  Sets first_seen_at on insert, last_seen_at on every see.
  Returns (inserted_count, updated_count).

  Uses INSERT OR IGNORE then UPDATE so we can count inserts vs updates correctly
  (SQLite rowcount is 1 for both insert and update in ON CONFLICT DO UPDATE).
  """
  if not jobs:
    return 0, 0
  now = datetime.now(timezone.utc).isoformat(timespec="seconds")
  inserted_total = 0
  updated_total = 0
  with get_conn() as conn:
    cur = conn.cursor()
    for job in jobs:
      row = {
        "title": job["title"],
        "company": job["company"],
        "location": job["location"],
        "source": job["source"],
        "role_type": job["role_type"],
        "posted_date_text": job.get("posted_date_text") or job.get("posted_date", ""),
        "posted_at": job.get("posted_at"),
        "apply_url": job["apply_url"],
        "scraped_at": now,
        "first_seen_at": now,
        "last_seen_at": now,
        "is_active": 1,
      }
      cur.execute(
        """
        INSERT OR IGNORE INTO jobs (
            title, company, location, source, role_type,
            posted_date_text, posted_at, apply_url, scraped_at,
            first_seen_at, last_seen_at, is_active
        )
        VALUES (
            :title, :company, :location, :source, :role_type,
            :posted_date_text, :posted_at, :apply_url, :scraped_at,
            :first_seen_at, :last_seen_at, :is_active
        )
        """,
        row,
      )
      if cur.rowcount == 1:
        inserted_total += 1
      else:
        cur.execute(
          """
          UPDATE jobs SET
              title = :title,
              company = :company,
              location = :location,
              role_type = :role_type,
              posted_date_text = :posted_date_text,
              posted_at = :posted_at,
              scraped_at = :scraped_at,
              last_seen_at = :last_seen_at,
              is_active = 1
          WHERE apply_url = :apply_url
          """,
          row,
        )
        if cur.rowcount >= 1:
          updated_total += 1
  return inserted_total, updated_total


if __name__ == "__main__":
  from .main import JOBS  # type: ignore

  init_db(sample_jobs=JOBS)
  print(f"Initialized database at {DB_PATH.resolve()} with {len(JOBS)} sample jobs.")
