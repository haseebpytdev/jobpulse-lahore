# JobPulse Lahore

JobPulse is a FastAPI application that aggregates job listings for Lahore and remote-friendly roles into a single searchable interface. It normalizes listings from multiple source adapters, persists them in SQLite, deduplicates repeated jobs, and exposes both browser and API workflows.

## What it demonstrates

- Multi-source ingestion with isolated adapters and failure handling
- Normalized persistence with URL-based deduplication and upserts
- Search and filtering by keyword, source, role, location, and freshness
- Source health/status reporting and controlled refreshes
- CSV export and JSON API workflows
- Tests for ingestion, duplicate handling, persistence, and core application behavior

## Sources

Adapters include Remotive, Remote OK, We Work Remotely, Rozee, Mustakbil, Glassdoor, GitHub Jobs, and Wellfound. Indeed and LinkedIn are retained as placeholders rather than presenting unsupported scraping as production-ready.

## Stack

- Python
- FastAPI
- SQLite
- Jinja2
- HTTPX / BeautifulSoup
- pytest

## Run locally

```bash
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the local URL shown by Uvicorn in your browser.

## Verification

The repository includes focused verification notes and automated tests covering source ingestion, normalization, deduplication, database upserts, and application flows.
