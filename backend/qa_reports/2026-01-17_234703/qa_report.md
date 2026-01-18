# QA Report

Generated: 2026-01-17T23:47:03.398031Z
## Checks
| Status | Check | Details |
|---|---|---|
| PASS | API health responds 200 |  |
| PASS | Auth register does not 500 |  |
| PASS | Auth login invalid creds does not 500 |  |
| FAIL | Auth + opportunities endpoints do not 500 | 500 on opportunities patch fake id: {   "error": "{'status': ['Must be one of: new, investigating, interested, dismissed.']}" }  |
| PASS | UI homepage loads |  |
| PASS | UI has Sign In link |  |
| PASS | UI has Signup/Get Started link |  |
| PASS | UI Sign In form has email/password/submit |  |
| PASS | UI Signup form has email/password/submit |  |
| PASS | UI Signup shows success/verify message |  |
| PASS | UI post-signup offers login |  |
| PASS | UI login redirect is acceptable |  |

## Notes
- Register status=201 (email=qa-77c27a78@example.com)
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- UI /dashboard guard inconclusive
