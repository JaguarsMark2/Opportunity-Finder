# QA Report

Generated: 2026-01-20T20:26:31.700169Z
## Checks
| Status | Check | Details |
|---|---|---|
| FAIL | API health responds 200 | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /health (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | Auth register does not 500 | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | Auth login invalid creds does not 500 | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | Token refresh flow works correctly | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | Logout invalidates refresh token correctly | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/user/profile returns user data | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | PATCH /api/v1/user/profile works (empty update) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/user/stats returns statistics | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/user/saved returns saved opportunities | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/opportunities with filters works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/opportunities with sorting works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/opportunities with search works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/opportunities with time_range works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/opportunities pagination works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | PATCH /api/v1/opportunities/<id> save/unsave works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | PATCH /api/v1/opportunities/<id> status update works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/scoring/config returns scoring configuration | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | POST /api/v1/scoring/opportunity/<id>/score works | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/admin/analytics works (admin) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/admin/users works (admin) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/admin/pricing works (admin) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/admin/health works (admin) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/scan/recent returns scan history (admin) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/scan/stats returns scan statistics (admin) | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | Non-admin users rejected from admin endpoints | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | API properly rejects malformed input | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | Rate limiting returns 429 when exhausted | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/login (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| FAIL | GET /api/v1/dashboard returns aggregated data | HTTPConnectionPool(host='127.0.0.1', port=5000): Max retries exceeded with url: /api/v1/auth/register (Caused by NewConnectionError("HTTPConnection(host='127.0.0.1', port=5000): Failed to establish a new connection: [Errno 111] Connection refused")) |
| PASS | UI homepage loads |  |
| PASS | UI has Sign In link |  |
| PASS | UI has Signup/Get Started link |  |
| PASS | UI Sign In form has email/password/submit |  |
| PASS | UI Signup form has email/password/submit |  |
| FAIL | UI Signup shows success/verify message | could not detect success/verify text |
| PASS | UI post-signup offers login |  |
| PASS | UI login redirect is acceptable |  |
| PASS | UI /dashboard accessible when authenticated |  |
| PASS | UI /dashboard guarded when not authenticated |  |

## Notes
- Homepage links=['OF\nOpportunity Finder', 'Sign In', 'Get Started', 'Get Started Free', 'Sign In', 'Start Free Trial']
- Homepage buttons=[]
- Post-login URL: http://localhost:5173/login
