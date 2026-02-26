## JobPulse Lahore

JobPulse Lahore is a **small FastAPI-powered job discovery dashboard** focused on **Python / Django / early‑career roles in Lahore**.  
It is intentionally simple and backend‑centric to clearly demonstrate server‑side filtering, templating, and deployment‑ready structure.

### What this MVP does

- **Landing page dashboard** at `/` built with:
  - **FastAPI** for routing and request handling.
  - **Jinja2 templates** for server‑side rendering.
  - A **single, styled dashboard view** (`dashboard.html`) showing a curated list of roles.
- **In‑memory job dataset** (Python list of dicts) in `app/main.py`:
  - Fields: `title`, `company`, `location`, `source`, `posted_date`, `apply_url`, `role_type`.
  - Designed so you can later swap the list out for a real database (PostgreSQL, SQLite, etc.).
- **Server‑side filtering via query params**:
  - `q` – free‑text search across job title and company.
  - `source` – e.g. `indeed`, `rozee`.
  - `role_type` – e.g. `intern`, `trainee`.
- **Stats panel** on the dashboard:
  - Total visible jobs.
  - Count of jobs “posted today”.
  - Number of distinct sources.
  - Last updated timestamp (generated on the server at each request).

### Tech stack

- **Python 3.13+**
- **FastAPI** – API framework and routing.
- **Starlette** – ASGI toolkit under FastAPI.
- **Uvicorn** – ASGI server.
- **Jinja2** – HTML templating.

All main dependencies are tracked in `requirements.txt`.

### Project structure

- `app/`
  - `main.py` – FastAPI application with:
    - `JOBS` in‑memory dataset.
    - `/` route (`dashboard`) with filter logic and stats aggregation.
  - `templates/`
    - `dashboard.html` – Jinja2 template for the main UI.
- `requirements.txt` – Python dependencies (FastAPI, Jinja2, Uvicorn, etc.).
- `setup-git.ps1` – helper script to initialize the repo and push to GitHub (optional).

### Running the project locally

1. **Create and activate a virtual environment (recommended)**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # PowerShell / CMD on Windows
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI app with Uvicorn**

   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open the dashboard**

   Visit:

   - `http://127.0.0.1:8000/`

### Using the filters

- **Search (`q`)**
  - Matches text in **job title** or **company** (case‑insensitive).
  - Example: `?q=python`, `?q=intern`, `?q=company`.

- **Source (`source`)**
  - Filters by `source` field.
  - Example: `?source=indeed`, `?source=rozee`.

- **Role type (`role_type`)**
  - Filters by job type.
  - Example: `?role_type=intern`, `?role_type=trainee`.

- **Combining filters**
  - All filters are applied server‑side on the in‑memory list.
  - Example: `/?q=python&source=indeed&role_type=intern`

The right sidebar on the dashboard exposes these filters via a simple HTML form using `GET`, so the resulting URLs are shareable and easily testable.

### How this can evolve

This MVP is intentionally small but structured so it can grow:

- Swap the `JOBS` list for a **database model** (SQLAlchemy, Tortoise, etc.).
- Add **scheduled scrapers** or **API integrations** for real job sources.
- Introduce **pagination** and additional filters (salary range, skills, experience).
- Add **authentication** and a simple **admin panel** for curating or hiding jobs.

### Git workflow for this repo

- **Main branch:** `main`
- **Commit style:** use descriptive, conventional commit‑style messages where possible, e.g.:
  - `chore: initial scaffold`
  - `feat: add FastAPI dashboard`
  - `docs: update README with setup guide`

For each important change (new routes, data sources, UI refinements), add a focused commit so the history clearly tells the story of how JobPulse Lahore evolved.

