from typing import Any, Dict, List, Mapping

from .db import get_conn


def list_jobs(
    q: str = "",
    source: str = "",
    role_type: str = "",
    location: str = "",
) -> List[Mapping[str, Any]]:
    """
    Repository layer for job queries.

    Hides raw SQL behind a small, focused API that:
    - Mirrors the current filter behaviour (q, source, role_type, location)
    - Returns dict-like rows suitable for templating (includes scraped_at for "new" badge)
    """
    sql_parts = [
        "SELECT title, company, location, source, role_type,",
        "       posted_date_text AS posted_date, apply_url, scraped_at",
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

    if location:
        loc_lower = location.lower()
        if loc_lower == "lahore":
            sql_parts.append("AND LOWER(location) LIKE ?")
            params.append("%lahore%")
        elif loc_lower == "remote":
            sql_parts.append("AND LOWER(location) LIKE ?")
            params.append("%remote%")

    sql_parts.append("ORDER BY scraped_at DESC, id DESC")
    query = " ".join(sql_parts)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]

