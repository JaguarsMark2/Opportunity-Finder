Opportunity Finder QA Suite

Runs:
- API smoke checks (50+ tests covering backend endpoints)
- UI smoke checks (selenium+chromedriver)

Outputs:
- qa_report.md (printed to stdout after run)

Features:
- User tracking workflow tests (status transitions, notes, isolation)
- Server connectivity checks with warnings
- Auth flow, admin endpoints, scoring, security tests

Run (from backend .venv):
python3 qa_suite/run_qa.py
