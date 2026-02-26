from datetime import datetime
import logging
import os
import time
from urllib.parse import urlencode, quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db, insert_jobs
from .repo import count_jobs, list_jobs
from .scrapers.github_jobs import scrape_github_jobs
from .scrapers.remoteok import scrape_remoteok_python
from .scrapers.rozee import scrape_rozee_python_lahore
from .scrapers.weworkremotely import scrape_weworkremotely

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


def _run_source(
    name: str,
    fetch_fn,
    insert_fn,
) -> tuple[int, int, str]:
    """Run one scraper; return (fetched, inserted, status_string)."""
    start = time.perf_counter()
    try:
        jobs = fetch_fn()
        inserted = insert_fn(jobs)
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "refresh source=%s fetched=%s inserted=%s duration_ms=%s",
            name, len(jobs), inserted, duration_ms,
        )
        return len(jobs), inserted, "ok"
    except Exception as e:  # noqa: BLE001
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.warning(
            "refresh source=%s error=%s duration_ms=%s",
            name, str(e), duration_ms,
        )
        return 0, 0, str(e)[:80].replace(" ", "_")


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
    jobs = list_jobs(
        q=q, source=source, role_type=role_type, location=location,
        limit=limit, offset=offset,
    )
    total = count_jobs(q=q, source=source, role_type=role_type, location=location)
    has_more = offset + len(jobs) < total
    total_pages = (total + limit - 1) // limit if limit else 1

    stats = {
        "total_jobs": total,
        "new_today": sum(1 for j in jobs if (j.get("posted_date") or "").lower() == "today"),
        "sources_count": len(set(j["source"] for j in jobs)),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    filters = {"q": q, "source": source, "role_type": role_type, "location": location, "days": days}
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

    export_params = {k: v for k, v in [("q", q), ("source", source), ("role_type", role_type), ("location", location)] if v}
    export_url = "/export.csv" + ("?" + urlencode(export_params) if export_params else "")
    load_more_params = [(k, v) for k, v in [("page", page + 1), ("q", q), ("source", source), ("role_type", role_type), ("location", location)] if v]
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
        },
    )


@app.post("/refresh")
@app.get("/refresh")
def refresh() -> RedirectResponse:
    """
    Run all scrapers with per-source try/except; rate limit 30s.
    Redirect with partial-success status (e.g. RemoteOK ok, Rozee blocked).
    """
    global _last_refresh_at
    now = time.perf_counter()
    if _last_refresh_at is not None and (now - _last_refresh_at) < REFRESH_COOLDOWN_SEC:
        logger.warning("refresh rate_limited cooldown_sec=%s", REFRESH_COOLDOWN_SEC)
        return RedirectResponse(
            url="/?rate_limited=1&refreshed=0",
            status_code=303,
        )

    status_parts: list[str] = []
    total_fetched = 0
    total_inserted = 0
    results = {}

    def run(name: str, fetch_fn, insert_fn):
        nonlocal total_fetched, total_inserted
        f, i, st = _run_source(name, fetch_fn, insert_fn)
        total_fetched += f
        total_inserted += i
        results[name] = (f, i, st)
        if st == "ok":
            status_parts.append(f"{name} ok")
        else:
            status_parts.append(f"{name} {st}")

    run("Rozee", lambda: scrape_rozee_python_lahore(max_pages=1, delay_sec=1.0), insert_jobs)
    run("RemoteOK", lambda: scrape_remoteok_python(limit=30), insert_jobs)
    run("WWR", lambda: scrape_weworkremotely(limit=50), insert_jobs)
    run("GitHubJobs", lambda: scrape_github_jobs(limit=30), insert_jobs)

    _last_refresh_at = time.perf_counter()
    refresh_status = ", ".join(status_parts)

    params = (
        f"?refreshed=1&fetched={total_fetched}&inserted={total_inserted}"
        f"&rozee_fetched={results['Rozee'][0]}&rozee_inserted={results['Rozee'][1]}"
        f"&remoteok_fetched={results['RemoteOK'][0]}&remoteok_inserted={results['RemoteOK'][1]}"
        f"&weworkremotely_fetched={results['WWR'][0]}&weworkremotely_inserted={results['WWR'][1]}"
        f"&github_jobs_fetched={results['GitHubJobs'][0]}&github_jobs_inserted={results['GitHubJobs'][1]}"
        f"&refresh_status={quote(refresh_status, safe='')}"
    )
    return RedirectResponse(url="/" + params, status_code=303)


@app.get("/export.csv", include_in_schema=False)
def export_csv(
    q: str = "",
    source: str = "",
    role_type: str = "",
    location: str = "",
):
    """Export jobs matching current filters as CSV."""
    import csv
    import io

    jobs = list_jobs(
        q=q, source=source, role_type=role_type, location=location,
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
