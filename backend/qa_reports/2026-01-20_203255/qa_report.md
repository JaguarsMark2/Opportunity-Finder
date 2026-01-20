# QA Report

Generated: 2026-01-20T20:32:55.394886Z
## Checks
| Status | Check | Details |
|---|---|---|
| PASS | API health responds 200 |  |
| PASS | Auth register does not 500 |  |
| PASS | Auth login invalid creds does not 500 |  |
| PASS | Token refresh flow works correctly |  |
| PASS | Logout invalidates refresh token correctly |  |
| PASS | GET /api/v1/user/profile returns user data |  |
| PASS | PATCH /api/v1/user/profile works (empty update) |  |
| PASS | GET /api/v1/user/stats returns statistics |  |
| PASS | GET /api/v1/user/saved returns saved opportunities |  |
| PASS | GET /api/v1/opportunities with filters works |  |
| PASS | GET /api/v1/opportunities with sorting works |  |
| PASS | GET /api/v1/opportunities with search works |  |
| PASS | GET /api/v1/opportunities with time_range works |  |
| PASS | GET /api/v1/opportunities pagination works |  |
| PASS | PATCH /api/v1/opportunities/<id> save/unsave works |  |
| PASS | PATCH /api/v1/opportunities/<id> status update works |  |
| PASS | GET /api/v1/scoring/config returns scoring configuration |  |
| PASS | POST /api/v1/scoring/opportunity/<id>/score works |  |
| PASS | GET /api/v1/admin/analytics works (admin) |  |
| PASS | GET /api/v1/admin/users works (admin) |  |
| PASS | GET /api/v1/admin/pricing works (admin) |  |
| PASS | GET /api/v1/admin/health works (admin) |  |
| PASS | GET /api/v1/scan/recent returns scan history (admin) |  |
| PASS | GET /api/v1/scan/stats returns scan statistics (admin) |  |
| PASS | Non-admin users rejected from admin endpoints |  |
| FAIL | API properly rejects malformed input | 500 on login with invalid JSON: {   "error": "Login failed" }  |
| PASS | Rate limiting returns 429 when exhausted |  |
| PASS | GET /api/v1/dashboard returns aggregated data |  |
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
- Register status=201 (email=qa-62a10887@example.com)
- Token refresh successful, new token received: eyJhbGciOiJIUzI1NiIs...
- User stats: saved=0, tracked=0
- Opportunity 8671a816... saved successfully
- Opportunity 8671a816... status updated to 'interested'
- Scoring config keys: ['weights', 'thresholds']
- Opportunity 8671a816... scored, result: {'breakdown': {'competition_score': 100, 'complexity_score': 35, 'demand_score': 104, 'revenue_score
- Rate limit not triggered in 15 attempts (limit may be higher)
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
