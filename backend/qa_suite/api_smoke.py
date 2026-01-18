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


def _expect_200(url):
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        raise Exception(f"{url} expected 200 got {r.status_code}: {r.text[:200]}")
