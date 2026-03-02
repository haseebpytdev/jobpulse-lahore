# Engine verification checklist

Run these on your machine to confirm the multi-source engine, dedupe, and insert/update counting work.

---

## Prerequisites

1. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```
2. Open `http://127.0.0.1:8000/` in your browser.

---

## A) Multi-source engine

**Steps**

1. In the browser, go to:
   ```
   http://127.0.0.1:8000/refresh?sources=remoteok,weworkremotely&limit=50
   ```
2. You should be redirected to `/`.

**Expected**

- Page loads with job list.
- **Sidebar → “Sources status”** shows exactly **2** sources (e.g. RemoteOK, WWR).
- Each source shows **timings** and **fetched / inserted** (e.g. “20 fetched, 3 inserted · 800ms”).

If you see two sources with real numbers and timings, the engine is running multi-source correctly.

---

## B) Dedupe (no duplicate rows)

**Steps**

1. Wait for the **30-second cooldown** after the first refresh (or wait 30s before step 2).
2. Click **“Refresh jobs”** again (or hit `/refresh` again with the same or no params).

**Expected**

- **Second run:** `fetched > 0` (scrapers ran).
- **Second run:** `inserted` is often **0** (or small), because most `apply_url`s already exist and are skipped on insert.

That confirms dedupe by `apply_url` is working.

---

## C) Inserted vs updated (upsert counting)

**Steps**

1. **First refresh:** run refresh once (e.g. click “Refresh jobs” or hit `/refresh`).
   - Note: some jobs are **inserted** (new `apply_url`s).
2. Wait **30 seconds** (cooldown).
3. **Second refresh:** run refresh again with the **same** sources (same jobs are re-fetched).

**Expected**

- **Second refresh:** `updated > 0` (existing rows had `last_seen_at` etc. updated).
- **Second refresh:** `inserted = 0` (no new URLs).

That’s the proof that insert vs update counting is correct and upserts are behaving as intended.

---

## Quick recap

| Check   | What to do                          | What you should see                          |
|--------|--------------------------------------|----------------------------------------------|
| **A**  | `/refresh?sources=remoteok,weworkremotely&limit=50` | Redirect to `/`, sidebar shows 2 sources with timings and fetched/inserted |
| **B**  | Refresh twice (after cooldown)       | Second run: fetched > 0, inserted often 0    |
| **C**  | Refresh once, then again after 30s   | Second run: updated > 0, inserted = 0       |
