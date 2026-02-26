from typing import Any, Dict, List, Mapping

from .db import get_conn


def list_jobs(
    q: str = "",
    source: str = "",
    role_type: str = "",
) -> List[Mapping[str, Any]]:
    """
    Repository layer for job queries.

    Hides raw SQL behind a small, focused API that:
    - Mirrors the current filter behaviour (q, source, role_type)
    - Returns dict-like rows suitable for templating
    """
    sql_parts = [
        "SELECT title, company, location, source, role_type,",
        "       posted_date_text AS posted_date, apply_url",
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

