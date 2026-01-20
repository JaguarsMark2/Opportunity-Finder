# QA Report

Generated: 2026-01-19T21:58:16.841044Z
## Checks
| Status | Check | Details |
|---|---|---|
| PASS | API health responds 200 |  |
| PASS | Auth register does not 500 |  |
| PASS | Auth login invalid creds does not 500 |  |
| PASS | Auth + opportunities endpoints do not 500 |  |
| FAIL | Dashboard route guard works correctly | dashboard authenticated expected 200 got 404: <!doctype html> <html lang=en> <title>404 Not Found</title> <h1>Not Found</h1> <p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try agai |
| PASS | Scan endpoint rejects non-admin users |  |
| FAIL | Admin can trigger scan and check progress | Scan progress returned 404 - scan not found (possible ID mismatch bug) |
| PASS | Scan progress with fake ID does not 500 |  |
| PASS | UI homepage loads |  |
| PASS | UI has Sign In link |  |
| PASS | UI has Signup/Get Started link |  |
| PASS | UI Sign In form has email/password/submit |  |
| PASS | UI Signup form has email/password/submit |  |
| PASS | UI Signup shows success/verify message |  |
| PASS | UI post-signup offers login |  |
| PASS | UI login redirect is acceptable |  |
| PASS | UI /dashboard accessible when authenticated |  |
| FAIL | UI /dashboard guarded when not authenticated | URL=http://localhost:5173/dashboard - page appears accessible without auth |

## Notes
- Register status=201 (email=qa-1ed8e428@example.com)
- Dashboard unauth status=404 (expected 401/403/redirect)
- Scan triggered: scan_id=7a0a19c6-c41a-4a84-8141-627d443165ee
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
