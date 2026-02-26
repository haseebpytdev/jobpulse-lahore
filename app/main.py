from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import init_db
from .repo import list_jobs

app = FastAPI(title="JobPulse Lahore")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
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
    """
    Ensure SQLite schema exists and seed with JOBS once.
    """
    init_db(sample_jobs=JOBS)


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

