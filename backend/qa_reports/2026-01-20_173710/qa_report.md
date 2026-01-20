# QA Report

Generated: 2026-01-20T17:37:10.233739Z
## Checks
| Status | Check | Details |
|---|---|---|
| FAIL | API health responds 200 | HTTPConnectionPool(host='127.0.0.1', port=5000): Read timed out. (read timeout=20) |
| PASS | Auth register does not 500 |  |
| FAIL | Auth login invalid creds does not 500 | unexpected status 429: {   "error": "Rate limit exceeded",   "retry_after": 94 }  |
| FAIL | Auth + opportunities endpoints do not 500 | login for auth-check expected 200 got 429: {   "error": "Rate limit exceeded",   "retry_after": 92 }  |
| FAIL | Dashboard route guard works correctly | login for dashboard check failed: {   "error": "Rate limit exceeded",   "retry_after": 92 }  |
| FAIL | Scan endpoint rejects non-admin users | login for scan admin check failed: {   "error": "Rate limit exceeded",   "retry_after": 92 }  |
| FAIL | Admin can trigger scan and check progress | admin login failed: 429 - {   "error": "Rate limit exceeded",   "retry_after": 92 }  |
| FAIL | Scan progress with fake ID does not 500 | login for fake scan check failed: {   "error": "Rate limit exceeded",   "retry_after": 91 }  |
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
- Register status=201 (email=qa-d74ca8fa@example.com)
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
