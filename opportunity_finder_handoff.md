# Opportunity Finder – Engineering Handoff (QA Suite + Scan/Progress Bug)

Generated: 2026-01-19

## 1) Context and Objective

You are inheriting a partially working Opportunity Finder app (Flask + SQLAlchemy + JWT + Celery + Redis; React/Vite frontend) that contains multiple broken or incomplete flows.

**Primary objective:** build and extend an internal **`qa_suite`** that can **evaluate the usability and functional integrity of the program itself**—repeatably—by running checkpoints and emitting actionable failures. The suite is not intended to auto-fix; it is intended to **surface where and why things break** so fixes can be applied systematically and regressions prevented.

### What “usability evaluation” means here
The suite should detect common user-facing and integration failures, such as:
- Broken auth flows and dead-ends (e.g., “check your email” with no way back to login)
- Auth-gated routes being accessible when they should not be
- Unexpected redirects (e.g., login landing on `/dashboard` when product requires a landing page)
- Core workflow failures (scan/collect → progress → opportunities)
- API routes returning 500s due to missing guards / invalid exception handling
- Rate-limit behaviors masking actual failures

---

## 2) Repo / Environment

- Repo: `https://github.com/JaguarsMark2/Opportunity-Finder`
- Local: Windows + WSL Ubuntu
- Backend: Flask, SQLAlchemy, Marshmallow, JWT, Celery, Redis
- Frontend: React (Vite)

---

## 3) Running the app (known baseline)

### Terminal A — Backend
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/backend
source .venv/bin/activate
python3 run.py
```

### Terminal B — Frontend
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/frontend
npm run dev
```

### Redis connectivity test (confirmed working)
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/backend
source .venv/bin/activate
python3 -c "from app.redis_client import redis_client; print(redis_client.ping())"
# True
```

### Terminal C — Celery Worker
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/backend
source .venv/bin/activate
PYTHONPATH=. celery -A app.celery_app worker --loglevel=info -Q scans,scoring,emails,celery
```

**OR use the provided script:**
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/backend
source .venv/bin/activate
./scripts/start_worker.sh
```

---

## 4) QA Suite – What it is and how it should evolve

### Purpose of `qa_suite`
`qa_suite` is the **automation harness** for evaluating the system’s usability and correctness:
- It executes a checklist of API and UI flows
- It outputs **timestamped** reports to prevent clutter and preserve run history
- It should highlight failures with:
  - endpoint/page
  - request/inputs used
  - observed response or DOM evidence
  - expected behavior
  - probable root cause location (file/function)

### Current location and outputs
- Suite: `backend/qa_suite/`
- Reports: `backend/qa_reports/YYYY-MM-DD_HHMMSS/qa_report.md`

### Current scope (implemented checkpoints)
- API health
- Auth register (must not 500)
- Auth login invalid creds (must not 500)
- Authenticated opportunities endpoints (GET list, GET stats, GET fake id should not 500, PATCH fake id should not 500)
- Basic UI checks:
  - homepage loads
  - presence of Sign In / Signup link
  - sign-in form has email/password/submit
  - sign-up form has email/password/submit
  - post-signup offers login path
  - login redirect acceptable (still needs a definitive requirement)

### Known improvements required to the suite
- Make `/dashboard` route guard check **definitive** (not “inconclusive”):
  - as anonymous user: expect redirect to login or 401/403
  - as authenticated: expect 200 + dashboard content
- Add end-to-end core workflow checks:
  - trigger scan (admin)
  - verify progress endpoint reflects the scan (not “not found”)
  - verify opportunities populated / changes observable
- Expand UX checks for “dead-end” states:
  - “Check your email” page must provide a clear “Back to login” or auto-redirect.

---

## 5) Fixed issues discovered and addressed during this session

### 5.1 Auth register 500 from QA (not from UI)
- **Root cause:** QA was sending `confirm_password` which backend `RegisterSchema` does not accept.
- **Outcome:** Frontend is correct (sends `{email,password}`); QA suite was fixed to match.

### 5.2 Opportunities PATCH route 500 (real backend bug)
- **Bug class:** exception path calls `db.close()` when `db` was not created or was `None`.
- **Symptoms:** 500 with `UnboundLocalError` / `NoneType has no attribute close`.
- **Fix applied:** guard `db.close()` in `update_opportunity()` and early return blocks.

### 5.3 QA PATCH payload was invalid
- QA used `status="ignored"` which fails schema validation.
- QA changed to a valid enum (`"new"`).

---

## 6) Admin / Roles – Current state and product gap

### Current behavior
`POST /api/v1/scan` is **admin-only**:
- `backend/app/api/scan.py` checks `user.role.value != 'admin'` then returns 403.

### Problem/gap
There is no UI or bootstrap mechanism to create/assign admin users.

### Dev workaround added
`backend/scripts/set_role.py` was created to set roles via CLI.

**Important:** because the backend isn’t treated as a package when running scripts, use:
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/backend
source .venv/bin/activate
PYTHONPATH=. python3 scripts/set_role.py <email> <USER|ADMIN>
```

### Recommended proper solution (to implement)
Add a **bootstrap admin** mechanism:
- Option A: env var `BOOTSTRAP_ADMIN_EMAIL` on startup (one-time)
- Option B: protected endpoint requiring a server-side secret for role assignment
- Option C: admin UI once a single admin exists

---

## 7) Critical urgent bug: Scan trigger returns “running” but progress says “Scan not found”

### Observed behavior
1) As admin, `POST /api/v1/scan` returns:
```json
{ "message": "Scan started", "scan_id": "<uuid>", "status": "running" }
```

2) Immediately querying:
`GET /api/v1/scan/<scan_id>`
returns:
```json
{ "error": "Scan not found" }
```

### Why this is happening (high confidence)
`POST /api/v1/scan` returns the **Celery task id** as `scan_id`:
- `task = run_scan.apply_async(args=[sources])`
- returns `scan_id = task.id`

But `GET /api/v1/scan/<scan_id>` looks for:
- Redis status via `get_scan_status(scan_id)` (likely key-based)
- DB row `Scan.id == scan_id` (fallback)

If the task is writing progress/DB rows under a **different id**, then:
- Redis lookup fails
- DB lookup fails
→ “Scan not found”

### Attempted fix
Change `run_scan` task to use Celery task id as scan id:
- `scan_id = self.request.id` (instead of `uuid.uuid4()`)

**Status:** user reports the flow still returns “Scan not found”, so additional inconsistencies likely remain:
- Writer uses different Redis key than reader expects
- Task never writes DB Scan row at all
- `get_scan_status` key format does not match
- Worker not reloading correct module path / stale code
- Task errors before persisting anything

### Deterministic next steps for an engineer/agent
1) In `backend/app/tasks/scan_tasks.py`, locate:
   - `get_scan_status(scan_id)` and note the Redis key pattern used.
2) Locate where scan progress is written (Redis + DB):
   - ensure it uses **exactly** the same `scan_id` and key pattern.
3) Decide on one consistent ID strategy:

**Strategy 1 (recommended): “scan_id == celery task id” everywhere**
- Trigger returns `task.id`
- Task writes Redis and DB using `task.id`
- Progress endpoint reads `task.id`

**Strategy 2: keep separate scan UUID but return it**
- Create Scan row synchronously before enqueueing
- Return the scan UUID, not task id

**Strategy 3: progress endpoint uses Celery AsyncResult**
- Accept task id and query Celery backend for state/progress

4) Add a QA suite check for scan/progress:
- POST `/api/v1/scan` returns 202 + scan_id
- GET `/api/v1/scan/<id>` returns 200 with status (not “not found”)
- optional polling until terminal state.

---

## 8) Rate limiting notes
Rate limiting has repeatedly masked real debugging (429s). For dev/QA:
- either increase limits significantly in dev, or
- configure limiter storage + reset behavior for tests, or
- add a `QA_MODE=1` bypass for known-safe routes used by the suite.

---

## 9) Practical operating guidance (to avoid burning time/tokens)
- Prefer improving `qa_suite` checks over manual clicking.
- When something fails, fix it by:
  - making endpoints return correct status codes (400/403/404 vs 500)
  - ensuring UI provides an escape path (no dead-ends)
  - writing a regression check into the suite.

---

## 10) Acceptance criteria for “scan flow working”
Minimum:
- Admin can trigger scan and receives a `scan_id`
- Progress endpoint returns status for that id (running/completed/failed), not “not found”
- Worker logs show task executes
- Opportunities list or stats show a measurable change after scan (even if “0 found” is valid, it must be consistent and properly reported)

---

## Appendix A — Useful commands

### Login to get token
```bash
curl -s -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"of2@best-spot.co.uk","password":"Test1234!"}'
```

### Trigger scan (admin) in one line (login + call)
```bash
TOKEN="$(curl -s -X POST http://127.0.0.1:5000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"of2@best-spot.co.uk","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")" && \
curl -s -X POST http://127.0.0.1:5000/api/v1/scan -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{}'
```

### Run QA suite
```bash
cd /mnt/c/AI-Projects/Opportunity-Finder/backend
source .venv/bin/activate
python3 qa_suite/run_qa.py
```

---

## Appendix B — Open items (not yet implemented)
- Proper admin bootstrap + admin UI/endpoint
- Scan/progress ID consistency fix (core urgent)
- Strong route guard tests (dashboard and other protected pages)
- Email provider configuration or dev-mode disable of email verification
- More “usability” assertions: navigation, dead-end detection, predictable post-login routing
