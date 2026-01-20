# QA Report

Generated: 2026-01-20T17:35:31.065965Z
## Checks
| Status | Check | Details |
|---|---|---|
| PASS | API health responds 200 |  |
| PASS | Auth register does not 500 |  |
| PASS | Auth login invalid creds does not 500 |  |
| PASS | Auth + opportunities endpoints do not 500 |  |
| FAIL | Dashboard route guard works correctly | 500 on dashboard authenticated: {   "error": "'Opportunity' object has no attribute 'estimated_revenue'" }  |
| FAIL | Scan endpoint rejects non-admin users | login for scan admin check failed: {   "error": "Rate limit exceeded",   "retry_after": 191 }  |
| FAIL | Admin can trigger scan and check progress | admin login failed: 429 - {   "error": "Rate limit exceeded",   "retry_after": 191 }  |
| FAIL | Scan progress with fake ID does not 500 | login for fake scan check failed: {   "error": "Rate limit exceeded",   "retry_after": 191 }  |
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
- Register status=201 (email=qa-47fdf3d6@example.com)
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
