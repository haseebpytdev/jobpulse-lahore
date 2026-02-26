from datetime import datetime
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db, insert_jobs
from .repo import list_jobs
from .scrapers.rozee import scrape_rozee_python_lahore

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
    days: str = "",
):
    """
    Server-side filtering using query params backed by SQLite.
    """
    jobs = list_jobs(q=q, source=source, role_type=role_type)

    stats = {
        "total_jobs": len(jobs),
        "new_today": sum(
            1 for j in jobs if j["posted_date"].lower() == "today"
        ),
        "sources_count": len(set(j["source"] for j in jobs)),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    filters = {"q": q, "source": source, "role_type": role_type, "days": days}

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "jobs": jobs, "stats": stats, "filters": filters},
    )


@app.post("/refresh")
def refresh() -> RedirectResponse:
    """
    Run Rozee scraper, write to DB, then redirect to dashboard.
    User sees updated jobs immediately without a second click.
    """
    jobs = scrape_rozee_python_lahore(max_pages=1, delay_sec=1.0)
    inserted = insert_jobs(jobs)
    print("SCRAPER fetched:", len(jobs), "Inserted:", inserted)
    return RedirectResponse(url="/", status_code=303)

