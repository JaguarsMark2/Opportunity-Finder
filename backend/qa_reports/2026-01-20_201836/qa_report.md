# QA Report

Generated: 2026-01-20T20:18:36.730647Z
## Checks
| Status | Check | Details |
|---|---|---|
| FAIL | API health responds 200 | HTTPConnectionPool(host='127.0.0.1', port=5000): Read timed out. (read timeout=20) |
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
| FAIL | PATCH /api/v1/opportunities/<id> save/unsave works | 500 on opportunity save: {   "error": "{'is_saved': ['Unknown field.']}" }  |
| PASS | PATCH /api/v1/opportunities/<id> status update works |  |
| PASS | GET /api/v1/scoring/config returns scoring configuration |  |
| PASS | POST /api/v1/scoring/opportunity/<id>/score works |  |
| FAIL | GET /api/v1/admin/analytics works (admin) | 500 on admin analytics: {   "error": "Database error: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum subscriptionstatus: \"trialing\"\nLINE 4: WHERE users.subscription_status = 'trialing') AS anon_1 |
| PASS | GET /api/v1/admin/users works (admin) |  |
| PASS | GET /api/v1/admin/pricing works (admin) |  |
| PASS | GET /api/v1/admin/health works (admin) |  |
| PASS | GET /api/v1/scan/recent returns scan history (admin) |  |
| PASS | GET /api/v1/scan/stats returns scan statistics (admin) |  |
| FAIL | Non-admin users rejected from admin endpoints | /api/v1/scoring/weights non-admin expected 403/401 got 405: <!doctype html> <html lang=en> <title>405 Method Not Allowed</title> <h1>Method Not Allowed</h1> <p>The method is not allowed for the requested URL.</p>  |
| FAIL | API properly rejects malformed input | 500 on register with invalid email: {   "error": "Registration failed" }  |
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
- Register status=201 (email=qa-998720e1@example.com)
- Token refresh successful, new token received: eyJhbGciOiJIUzI1NiIs...
- User stats: saved=0, tracked=0
- Opportunity 0c0b8425... status updated to 'interested'
- Scoring config keys: ['weights', 'thresholds']
- Opportunity 0c0b8425... scored, result: {'breakdown': {'competition_score': 100, 'complexity_score': 20, 'demand_score': 109, 'revenue_score
- Rate limit not triggered in 15 attempts (limit may be higher)
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
