# QA Report

Generated: 2026-01-17T23:37:13.305291Z
## Checks
| Status | Check | Details |
|---|---|---|
| PASS | API health responds 200 |  |
| PASS | Auth register does not 500 |  |
| PASS | Auth login invalid creds does not 500 |  |
| FAIL | Auth + opportunities endpoints do not 500 | 500 on opportunities patch fake id: <!doctype html> <html lang=en>   <head>     <title>AttributeError: &#39;NoneType&#39; object has no attribute &#39;close&#39;  // Werkzeug Debugger</title>     <link rel="stylesheet" href="?__debugger |
| PASS | UI homepage loads |  |
| PASS | UI has Sign In link |  |
| PASS | UI has Signup/Get Started link |  |
| PASS | UI Sign In form has email/password/submit |  |
| PASS | UI Signup form has email/password/submit |  |
| PASS | UI Signup shows success/verify message |  |
| PASS | UI post-signup offers login |  |
| PASS | UI login redirect is acceptable |  |

## Notes
- Register status=201 (email=qa-7627d696@example.com)
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- UI /dashboard guard inconclusive
