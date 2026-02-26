from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="JobPulse Lahore")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# MVP data: hardcoded list (replace later with DB)
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


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    q: str = "",
    source: str = "",
    role_type: str = "",
    days: str = "",
):
    """
    Server-side filtering using query params.
    Why: Simple, robust, and proves backend competency.
    """
    filtered = JOBS

    if q:
        q_lower = q.lower()
        filtered = [
            j
            for j in filtered
            if q_lower in j["title"].lower() or q_lower in j["company"].lower()
        ]
    if source:
        filtered = [j for j in filtered if j["source"] == source]
    if role_type:
        filtered = [j for j in filtered if j["role_type"] == role_type]

    stats = {
        "total_jobs": len(filtered),
        "new_today": sum(
            1 for j in filtered if j["posted_date"].lower() == "today"
        ),
        "sources_count": len(set(j["source"] for j in filtered)),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    filters = {"q": q, "source": source, "role_type": role_type, "days": days}

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "jobs": filtered, "stats": stats, "filters": filters},
    )

