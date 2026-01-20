# QA Report

Generated: 2026-01-20T18:07:18.743183Z
## Checks
| Status | Check | Details |
|---|---|---|
| PASS | API health responds 200 |  |
| PASS | Auth register does not 500 |  |
| PASS | Auth login invalid creds does not 500 |  |
| PASS | Auth + opportunities endpoints do not 500 |  |
| PASS | Dashboard route guard works correctly |  |
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
| PASS | UI /dashboard guarded when not authenticated |  |

## Notes
- Register status=201 (email=qa-0f84a172@example.com)
- Scan triggered: scan_id=b3152b5c-8ba5-46ad-a494-70baa3f3724f
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
