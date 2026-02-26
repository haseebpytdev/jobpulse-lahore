from datetime import datetime, timedelta, timezone
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db, insert_jobs
from .repo import list_jobs
from .scrapers.github_jobs import scrape_github_jobs
from .scrapers.remoteok import scrape_remoteok_python
from .scrapers.rozee import scrape_rozee_python_lahore
from .scrapers.weworkremotely import scrape_weworkremotely

app = FastAPI(title="JobPulse Lahore")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Avoid 404 when the browser requests a favicon."""
    return Response(status_code=204)


templates = Jinja2Templates(directory="app/templates")

# MVP data: hardcoded list (used to seed DB on first run)
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
    days: str = "",
    refreshed: str = "",
    fetched: str = "",
    inserted: str = "",
    rozee_fetched: str = "",
    rozee_inserted: str = "",
    remoteok_fetched: str = "",
    remoteok_inserted: str = "",
    weworkremotely_fetched: str = "",
    weworkremotely_inserted: str = "",
    github_jobs_fetched: str = "",
    github_jobs_inserted: str = "",
):
    """
    Server-side filtering using query params backed by SQLite.
    refreshed/fetched/inserted and rozee_*/remoteok_* come from redirect after /refresh.
    """
    jobs = list_jobs(q=q, source=source, role_type=role_type, location=location)

    # Mark jobs added in the last 48h as "new" for highlighting
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    for j in jobs:
        j["is_new"] = False
        raw = j.get("scraped_at")
        if raw:
            try:
                # scraped_at is ISO string (e.g. 2026-02-26T12:00:00)
                if raw.endswith("Z"):
                    raw = raw.replace("Z", "+00:00")
                t = datetime.fromisoformat(raw)
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                j["is_new"] = t >= cutoff
            except (ValueError, TypeError):
                pass

    stats = {
        "total_jobs": len(jobs),
        "new_today": sum(
            1 for j in jobs if j["posted_date"].lower() == "today"
        ),
        "sources_count": len(set(j["source"] for j in jobs)),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    filters = {"q": q, "source": source, "role_type": role_type, "location": location, "days": days}
    flash = {
        "refreshed": refreshed,
        "fetched": fetched,
        "inserted": inserted,
        "rozee_fetched": rozee_fetched,
        "rozee_inserted": rozee_inserted,
        "remoteok_fetched": remoteok_fetched,
        "remoteok_inserted": remoteok_inserted,
        "weworkremotely_fetched": weworkremotely_fetched,
        "weworkremotely_inserted": weworkremotely_inserted,
        "github_jobs_fetched": github_jobs_fetched,
        "github_jobs_inserted": github_jobs_inserted,
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "jobs": jobs,
            "stats": stats,
            "filters": filters,
            "flash": flash,
        },
    )


@app.post("/refresh")
@app.get("/refresh")
def refresh() -> RedirectResponse:
    """
    Run all scrapers (Rozee, RemoteOK, We Work Remotely, GitHub Jobs),
    write to DB, redirect with per-source counts.
    """
    rozee_jobs = scrape_rozee_python_lahore(max_pages=1, delay_sec=1.0)
    remoteok_jobs = scrape_remoteok_python(limit=30)
    weworkremotely_jobs = scrape_weworkremotely(limit=50)
    github_jobs = scrape_github_jobs(limit=30)

    rozee_inserted = insert_jobs(rozee_jobs)
    remoteok_inserted = insert_jobs(remoteok_jobs)
    weworkremotely_inserted = insert_jobs(weworkremotely_jobs)
    github_jobs_inserted = insert_jobs(github_jobs)

    print("SCRAPER Rozee fetched:", len(rozee_jobs), "inserted:", rozee_inserted)
    print("SCRAPER RemoteOK fetched:", len(remoteok_jobs), "inserted:", remoteok_inserted)
    print(
        "SCRAPER We Work Remotely fetched:",
        len(weworkremotely_jobs),
        "inserted:",
        weworkremotely_inserted,
    )
    print("SCRAPER GitHub Jobs fetched:", len(github_jobs), "inserted:", github_jobs_inserted)

    total_fetched = (
        len(rozee_jobs)
        + len(remoteok_jobs)
        + len(weworkremotely_jobs)
        + len(github_jobs)
    )
    total_inserted = (
        rozee_inserted
        + remoteok_inserted
        + weworkremotely_inserted
        + github_jobs_inserted
    )

    params = (
        f"?refreshed=1"
        f"&fetched={total_fetched}&inserted={total_inserted}"
        f"&rozee_fetched={len(rozee_jobs)}&rozee_inserted={rozee_inserted}"
        f"&remoteok_fetched={len(remoteok_jobs)}&remoteok_inserted={remoteok_inserted}"
        f"&weworkremotely_fetched={len(weworkremotely_jobs)}&weworkremotely_inserted={weworkremotely_inserted}"
        f"&github_jobs_fetched={len(github_jobs)}&github_jobs_inserted={github_jobs_inserted}"
    )
    return RedirectResponse(url="/" + params, status_code=303)

