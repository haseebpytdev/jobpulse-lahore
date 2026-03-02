from datetime import datetime
import logging
import os
import time
from urllib.parse import urlencode, quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db, upsert_jobs
from .engine import run_engine, RunReport, SourceResult
from .repo import count_jobs, list_jobs
from .scrapers.registry import SOURCE_DISPLAY_NAMES

# --- Structured logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JobPulse Lahore")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

REFRESH_COOLDOWN_SEC = 30
_last_refresh_at: float | None = None
_last_run_report: RunReport | None = None

@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Avoid 404 when the browser requests a favicon."""
    return Response(status_code=204)


templates = Jinja2Templates(directory="app/templates")

JOBS = [
    {
        "title": "Python Intern",
        "company": "Example Co",
        "location": "Lahore",
        "source": "indeed",
        "posted_date": "Today",
        "apply_url": "https://example.com",
        "role_type": "intern",
    },
    {
        "title": "Django Trainee Developer",
        "company": "Sample Ltd",
        "location": "Lahore",
        "source": "rozee",
        "posted_date": "2 days ago",
        "apply_url": "https://example.com",
        "role_type": "trainee",
    },
]


@app.on_event("startup")
def bootstrap_db() -> None:
    """Schema always created; seed only when SEED_DB=true."""
    if os.getenv("SEED_DB") == "true":
        init_db(sample_jobs=JOBS)
    else:
        init_db()


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    q: str = "",
    source: str = "",
    role_type: str = "",
    location: str = "",
    page: int = 1,
    limit: int = 20,
    days: str = "",
    refreshed: str = "",
    fetched: str = "",
    inserted: str = "",
    refresh_status: str = "",
    rozee_fetched: str = "",
    rozee_inserted: str = "",
    remoteok_fetched: str = "",
    remoteok_inserted: str = "",
    weworkremotely_fetched: str = "",
    weworkremotely_inserted: str = "",
    github_jobs_fetched: str = "",
    github_jobs_inserted: str = "",
    rate_limited: str = "",
):
    """Dashboard with filters, pagination, and refresh flash."""
    offset = (page - 1) * limit
    freshness = days.strip().lower() if days else ""
    if freshness not in ("new_today", "last_3_days"):
        freshness = ""
    jobs = list_jobs(
        q=q, source=source, role_type=role_type, location=location,
        freshness=freshness,
        limit=limit, offset=offset,
    )
    total = count_jobs(q=q, source=source, role_type=role_type, location=location, freshness=freshness)
    has_more = offset + len(jobs) < total
    total_pages = (total + limit - 1) // limit if limit else 1

    stats = {
        "total_jobs": total,
        "new_today": sum(1 for j in jobs if j.get("is_new")),
        "sources_count": len(set(j["source"] for j in jobs)),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    filters = {"q": q, "source": source, "role_type": role_type, "location": location, "days": days, "freshness": freshness}
    flash = {
        "refreshed": refreshed,
        "fetched": fetched,
        "inserted": inserted,
        "refresh_status": refresh_status,
        "rozee_fetched": rozee_fetched,
        "rozee_inserted": rozee_inserted,
        "remoteok_fetched": remoteok_fetched,
        "remoteok_inserted": remoteok_inserted,
        "weworkremotely_fetched": weworkremotely_fetched,
        "weworkremotely_inserted": weworkremotely_inserted,
        "github_jobs_fetched": github_jobs_fetched,
        "github_jobs_inserted": github_jobs_inserted,
        "rate_limited": rate_limited,
    }

    export_params = {k: v for k, v in [("q", q), ("source", source), ("role_type", role_type), ("location", location), ("days", days)] if v}
    export_url = "/export.csv" + ("?" + urlencode(export_params) if export_params else "")
    load_more_params = [(k, v) for k, v in [("page", page + 1), ("q", q), ("source", source), ("role_type", role_type), ("location", location), ("days", days)] if v]
    load_more_url = "/?" + urlencode(load_more_params)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "jobs": jobs,
            "stats": stats,
            "filters": filters,
            "flash": flash,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_more": has_more,
            "export_url": export_url,
            "load_more_url": load_more_url,
            "run_report": _last_run_report,
        },
    )


@app.post("/refresh")
@app.get("/refresh")
def refresh(
    sources: str = "",
    limit: int = 50,
    query: str = "",
    location: str = "",
) -> RedirectResponse:
    """
    Run scrapers via the engine. Params: sources=remoteok,weworkremotely (comma-separated),
    limit=50, query=python, location=remote. Rate limit 30s.
    """
    global _last_refresh_at, _last_run_report
    now = time.perf_counter()
    if _last_refresh_at is not None and (now - _last_refresh_at) < REFRESH_COOLDOWN_SEC:
        logger.warning("refresh rate_limited cooldown_sec=%s", REFRESH_COOLDOWN_SEC)
        return RedirectResponse(
            url="/?rate_limited=1&refreshed=0",
            status_code=303,
        )

    source_list = [s.strip() for s in sources.split(",") if s.strip()]
    report = run_engine(
        sources=source_list if source_list else None,
        query=query.strip(),
        location=location.strip(),
        limit=min(limit, 200),
    )
    _last_run_report = report
    _last_refresh_at = time.perf_counter()

    params = (
        f"?refreshed=1&fetched={report.total_fetched}&inserted={report.total_inserted}"
        f"&refresh_status={quote(report.status_summary, safe='')}"
    )
    for r in report.results:
        key = r.source_key
        params += f"&{key}_fetched={r.fetched}&{key}_inserted={r.inserted}"
    return RedirectResponse(url="/" + params, status_code=303)


@app.get("/export.csv", include_in_schema=False)
def export_csv(
    q: str = "",
    source: str = "",
    role_type: str = "",
    location: str = "",
    days: str = "",
):
    """Export jobs matching current filters as CSV."""
    import csv
    import io

    freshness = days.strip().lower() if days else ""
    if freshness not in ("new_today", "last_3_days"):
        freshness = ""
    jobs = list_jobs(
        q=q, source=source, role_type=role_type, location=location,
        freshness=freshness,
        limit=10000, offset=0,
    )
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["title", "company", "location", "source", "role_type", "posted_date", "apply_url"])
    for j in jobs:
        w.writerow([
            j.get("title", ""),
            j.get("company", ""),
            j.get("location", ""),
            j.get("source", ""),
            j.get("role_type", ""),
            j.get("posted_date", ""),
            j.get("apply_url", ""),
        ])
    body = out.getvalue()
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobs.csv"},
    )
