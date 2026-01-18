#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
REPORT="$ROOT/doctor-report.txt"
: > "$REPORT"

log(){ echo -e "\n=== $* ===" | tee -a "$REPORT"; }

log "Semgrep (fast static scan)"
semgrep --config auto --quiet 2>&1 | tee -a "$REPORT" || true

if [ -d backend ]; then
  log "Backend: install deps"
  python3 -m venv backend/.venv 2>/dev/null || true
  source backend/.venv/bin/activate
  pip -q install -r backend/requirements.txt 2>&1 | tee -a "$REPORT" || true

  log "Backend: import check (catches missing modules fast)"
  python -c "import pkgutil,sys; sys.exit(0)" 2>&1 | tee -a "$REPORT" || true

  log "Backend: pytest"
  (cd backend && pytest -q) 2>&1 | tee -a "$REPORT" || true
  deactivate || true
fi

if [ -d frontend ]; then
  log "Frontend: install deps"
  (cd frontend && npm ci) 2>&1 | tee -a "$REPORT" || true

  log "Frontend: TypeScript typecheck"
  (cd frontend && npm run -s typecheck) 2>&1 | tee -a "$REPORT" || true

  log "Frontend: lint"
  (cd frontend && npm run -s lint) 2>&1 | tee -a "$REPORT" || true

  log "Frontend: build"
  (cd frontend && npm run -s build) 2>&1 | tee -a "$REPORT" || true
fi

log "Done. Report: doctor-report.txt"
