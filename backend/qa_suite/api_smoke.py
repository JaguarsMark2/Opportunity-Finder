"""API smoke tests for Opportunity Finder backend.

Comprehensive API tests including:
- Basic health and auth checks
- Authenticated opportunities endpoints
- Dashboard route guard checks (authenticated vs unauthenticated)
- End-to-end scan/progress workflow checks
- Admin-only endpoints verification
"""

import time
import uuid
import requests


def run_api_checks(cfg, report):
    base = cfg["backend_url"].rstrip("/")

    def check(name, fn):
        try:
            fn()
            report.pass_(name)
        except Exception as e:
            report.fail(name, str(e))

    check("API health responds 200", lambda: _expect_200(f"{base}/health"))

    # Register: 201/200 OK, 400 is acceptable (validation/duplicate), 500 is a bug.
    def register_check():
        email = f"qa-{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": email,
            "password": cfg["smoke_user_password"],
        }
        r = requests.post(f"{base}/api/v1/auth/register", json=payload, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on register: {r.text[:200]}")
        if r.status_code not in (201, 200, 400):
            raise Exception(f"unexpected status {r.status_code}: {r.text[:200]}")
        report.note(f"Register status={r.status_code} (email={email})")

    check("Auth register does not 500", register_check)

    # Login with invalid creds should not 500.
    def login_wrong_pw():
        payload = {"email": "nonexistent@example.com", "password": "wrongpw"}
        r = requests.post(f"{base}/api/v1/auth/login", json=payload, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on login: {r.text[:200]}")
        if r.status_code not in (401, 400):
            raise Exception(f"unexpected status {r.status_code}: {r.text[:200]}")

    check("Auth login invalid creds does not 500", login_wrong_pw)

    # Authenticated checks: login -> opportunities endpoints
    def auth_opps_checks():
        # Register a fresh user, then login, then call protected endpoints
        email = f"qa-auth-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]
        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        if r.status_code not in (201, 200, 400):
            raise Exception(f"register for auth-check unexpected {r.status_code}: {r.text[:200]}")

        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login for auth-check expected 200 got {r.status_code}: {r.text[:200]}")
        token = r.json().get("access_token")
        if not token:
            raise Exception("login response missing access_token")

        headers = {"Authorization": f"Bearer {token}"}

        # GET /opportunities
        r = requests.get(f"{base}/api/v1/opportunities", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities list: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities list expected 200 got {r.status_code}: {r.text[:200]}")

        # GET /opportunities/stats
        r = requests.get(f"{base}/api/v1/opportunities/stats", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities stats: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities stats expected 200 got {r.status_code}: {r.text[:200]}")

        # GET /opportunities/<id> with fake id should not 500
        r = requests.get(f"{base}/api/v1/opportunities/not-a-real-id", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities get fake id: {r.text[:200]}")

        # PATCH /opportunities/<id> fake id should not 500
        r = requests.patch(f"{base}/api/v1/opportunities/not-a-real-id", headers=headers, json={"status":"new"}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities patch fake id: {r.text[:200]}")

    check("Auth + opportunities endpoints do not 500", auth_opps_checks)

    # Dashboard guard checks
    def dashboard_guard_checks():
        # Unauthenticated: should redirect or return 401/403
        r = requests.get(f"{base}/api/v1/dashboard", timeout=20, allow_redirects=False)
        if r.status_code == 500:
            raise Exception(f"500 on dashboard unauthenticated: {r.text[:200]}")
        if r.status_code not in (401, 403, 302, 301):
            report.note(f"Dashboard unauth status={r.status_code} (expected 401/403/redirect)")

        # Authenticated: should return 200 with data
        email = f"qa-dash-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]
        requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login for dashboard check failed: {r.text[:200]}")
        token = r.json().get("access_token")
        if not token:
            raise Exception("login response missing access_token")

        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base}/api/v1/dashboard", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on dashboard authenticated: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"dashboard authenticated expected 200 got {r.status_code}: {r.text[:200]}")

        # Verify response has expected structure
        data = r.json()
        if not isinstance(data, dict):
            raise Exception(f"dashboard response not a dict: {type(data)}")

    check("Dashboard route guard works correctly", dashboard_guard_checks)

    # Scan endpoint admin-only check
    def scan_admin_check():
        # Non-admin should get 403
        email = f"qa-scan-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]
        requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login for scan admin check failed: {r.text[:200]}")
        token = r.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(f"{base}/api/v1/scan", headers=headers, json={}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on scan trigger (non-admin): {r.text[:200]}")
        if r.status_code != 403:
            raise Exception(f"scan trigger non-admin expected 403 got {r.status_code}: {r.text[:200]}")

    check("Scan endpoint rejects non-admin users", scan_admin_check)

    # Admin user creation and scan trigger (if admin email provided)
    if cfg.get("admin_email"):
        def admin_scan_workflow():
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            # Login as admin
            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.status_code} - {r.text[:200]}")
            token = r.json().get("access_token")
            if not token:
                raise Exception("admin login response missing access_token")

            headers = {"Authorization": f"Bearer {token}"}

            # Trigger scan
            r = requests.post(f"{base}/api/v1/scan", headers=headers, json={}, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on scan trigger (admin): {r.text[:200]}")
            if r.status_code not in (202, 200):
                raise Exception(f"scan trigger expected 202 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            scan_id = data.get("scan_id")
            if not scan_id:
                raise Exception(f"scan response missing scan_id: {r.text[:200]}")

            report.note(f"Scan triggered: scan_id={scan_id}")

            # Check progress endpoint
            r = requests.get(f"{base}/api/v1/scan/{scan_id}", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on scan progress: {r.text[:200]}")

            if r.status_code == 404:
                raise Exception(f"Scan progress returned 404 - scan not found (possible ID mismatch bug)")

            if r.status_code != 200:
                raise Exception(f"scan progress expected 200 got {r.status_code}: {r.text[:200]}")

            progress_data = r.json()
            report.note(f"Scan progress: status={progress_data.get('status')}, progress={progress_data.get('progress')}")

            # Wait a bit and check again
            time.sleep(2)
            r = requests.get(f"{base}/api/v1/scan/{scan_id}", headers=headers, timeout=20)
            if r.status_code == 200:
                progress_data = r.json()
                report.note(f"Scan progress (2s): status={progress_data.get('status')}, progress={progress_data.get('progress')}")

        check("Admin can trigger scan and check progress", admin_scan_workflow)
    else:
        report.note("Admin scan workflow skipped - no admin_email in config")

    # Scan progress with fake ID should not 500
    def scan_progress_fake_id():
        email = f"qa-fake-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]
        requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login for fake scan check failed: {r.text[:200]}")
        token = r.json().get("access_token")

        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{base}/api/v1/scan/fake-scan-id-123", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on scan progress fake id: {r.text[:200]}")
        if r.status_code not in (404, 200):
            raise Exception(f"scan progress fake id unexpected status {r.status_code}: {r.text[:200]}")

    check("Scan progress with fake ID does not 500", scan_progress_fake_id)


def _expect_200(url):
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        raise Exception(f"{url} expected 200 got {r.status_code}: {r.text[:200]}")
