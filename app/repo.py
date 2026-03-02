from typing import Any, Dict, List, Mapping

from .db import db_conn


def list_jobs(
    q: str = "",
    source: str = "",
    role_type: str = "",
    location: str = "",
    freshness: str = "",
    limit: int = 50,
    offset: int = 0,
) -> List[Mapping[str, Any]]:
    """
    Repository layer for job queries.

    - freshness: "" = any, "new_today" = first_seen in last 24h, "last_3_days" = first_seen in last 72h.
    - Returns dict-like rows with is_new = 1 if first_seen_at in last 24h.
    """
    sql_parts = [
        "SELECT title, company, location, source, role_type,",
        "       posted_date_text AS posted_date, apply_url, scraped_at,",
        "       first_seen_at, last_seen_at,",
        "       CASE WHEN datetime(COALESCE(first_seen_at, scraped_at)) >= datetime('now', '-1 day') THEN 1 ELSE 0 END AS is_new",
        "FROM jobs",
        "WHERE is_active = 1",
    ]
    params: List[object] = []

    if freshness == "new_today":
        sql_parts.append("AND datetime(COALESCE(first_seen_at, scraped_at)) >= datetime('now', '-1 day')")
    elif freshness == "last_3_days":
        sql_parts.append("AND datetime(COALESCE(first_seen_at, scraped_at)) >= datetime('now', '-3 days')")

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

    if location:
        loc_lower = location.lower()
        if loc_lower == "lahore":
            sql_parts.append("AND LOWER(location) LIKE ?")
            params.append("%lahore%")
        elif loc_lower == "remote":
            sql_parts.append("AND LOWER(location) LIKE ?")
            params.append("%remote%")

    sql_parts.append("ORDER BY scraped_at DESC, id DESC")
    sql_parts.append("LIMIT ? OFFSET ?")
    params.extend([limit, offset])
    query = " ".join(sql_parts)

    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def count_jobs(
    q: str = "",
    source: str = "",
    role_type: str = "",
    location: str = "",
    freshness: str = "",
) -> int:
    """Return total number of jobs matching the same filters as list_jobs (for pagination)."""
    sql_parts = ["SELECT COUNT(*) FROM jobs", "WHERE is_active = 1"]
    params: List[object] = []

    if freshness == "new_today":
        sql_parts.append("AND datetime(COALESCE(first_seen_at, scraped_at)) >= datetime('now', '-1 day')")
    elif freshness == "last_3_days":
        sql_parts.append("AND datetime(COALESCE(first_seen_at, scraped_at)) >= datetime('now', '-3 days')")

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
    if location:
        loc_lower = location.lower()
        if loc_lower == "lahore":
            sql_parts.append("AND LOWER(location) LIKE ?")
            params.append("%lahore%")
        elif loc_lower == "remote":
            sql_parts.append("AND LOWER(location) LIKE ?")
            params.append("%remote%")

    query = " ".join(sql_parts)
    with db_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()[0]

