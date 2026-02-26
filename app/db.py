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


def init_db(sample_jobs: Optional[List[Mapping[str, Any]]] = None) -> None:
  """
  Initialize SQLite schema and optional seed data.

  - One command for recruiters: run this once and the DB is ready.
  - UNIQUE(apply_url) prevents duplicate inserts automatically.
  - Indexes on source / role_type / scraped_at keep filters fast.
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
          scraped_at       TEXT NOT NULL
      );
      """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);")
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_jobs_role_type ON jobs(role_type);"
    )
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at);"
    )

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
            scraped_at
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
            :scraped_at
        );
        """,
        payload,
      )


def fetch_jobs(
  q: str = "",
  source: str = "",
  role_type: str = "",
) -> List[Mapping[str, Any]]:
  """
  RAW SQL filtering that mirrors the current in-memory behaviour.
  """
  sql_parts = [
    "SELECT title, company, location, source, role_type, posted_date_text AS posted_date, apply_url",
    "FROM jobs",
    "WHERE 1=1",
  ]
  params: List[object] = []

  if q:
    sql_parts.append("AND (LOWER(title) LIKE ? OR LOWER(company) LIKE ?)")
    pattern = f"%{q.lower()}%"
    params.extend([pattern, pattern])

  if source:
    sql_parts.append("AND source = ?")
    params.append(source)

  if role_type:
    sql_parts.append("AND role_type = ?")
    params.append(role_type)

  sql_parts.append("ORDER BY scraped_at DESC, id DESC")
  query = " ".join(sql_parts)

  with get_conn() as conn:
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
  from .main import JOBS  # type: ignore

  init_db(sample_jobs=JOBS)
  print(f"Initialized database at {DB_PATH.resolve()} with {len(JOBS)} sample jobs.")
