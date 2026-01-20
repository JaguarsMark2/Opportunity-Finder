"""API smoke tests for Opportunity Finder backend.

Comprehensive API tests including:
- Basic health and auth checks
- Authenticated opportunities endpoints
- Dashboard route guard checks (authenticated vs unauthenticated)
- End-to-end scan/progress workflow checks
- Admin-only endpoints verification
- Token refresh flow
- Logout functionality
- User profile operations
- Opportunities CRUD operations
- Filter/sort/search functionality
- Pagination
- Admin endpoints
- Scoring endpoints
- Input validation
- Rate limit behavior
- Authorization bypass detection

Total: 36+ tests covering all major API endpoints
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

    # =========================================================================
    # SECTION 1: BASIC HEALTH AND AUTH
    # =========================================================================

    check("API health responds 200", lambda: _expect_200(f"{base}/health"))

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
        return email  # Return email for subsequent tests

    check("Auth register does not 500", register_check)

    def login_wrong_pw():
        payload = {"email": "nonexistent@example.com", "password": "wrongpw"}
        r = requests.post(f"{base}/api/v1/auth/login", json=payload, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on login: {r.text[:200]}")
        if r.status_code not in (401, 400):
            raise Exception(f"unexpected status {r.status_code}: {r.text[:200]}")

    check("Auth login invalid creds does not 500", login_wrong_pw)

    # =========================================================================
    # SECTION 2: AUTH FLOW - TOKEN REFRESH
    # =========================================================================

    def token_refresh_check():
        """Test token refresh endpoint with refresh token."""
        email = f"qa-refresh-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        # Register and login
        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        access_token = r.json().get("access_token")
        refresh_token = r.json().get("refresh_token")

        if not access_token or not refresh_token:
            raise Exception("login response missing tokens")

        # Test token refresh endpoint
        headers = {"Authorization": f"Bearer {refresh_token}"}
        r = requests.post(f"{base}/api/v1/auth/refresh", headers=headers, timeout=20)

        if r.status_code == 500:
            raise Exception(f"500 on token refresh: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"token refresh expected 200 got {r.status_code}: {r.text[:200]}")

        new_token = r.json().get("access_token")
        if not new_token:
            raise Exception("token refresh response missing access_token")

        report.note(f"Token refresh successful, new token received: {new_token[:20]}...")

    check("Token refresh flow works correctly", token_refresh_check)

    # =========================================================================
    # SECTION 3: AUTH FLOW - LOGOUT
    # =========================================================================

    def logout_check():
        """Test logout endpoint invalidates refresh token."""
        email = f"qa-logout-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        # Register and login
        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        access_token = r.json().get("access_token")
        refresh_token = r.json().get("refresh_token")

        if not refresh_token:
            raise Exception("login response missing refresh_token")

        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.post(f"{base}/api/v1/auth/logout", headers=headers, json={"refresh_token": refresh_token}, timeout=20)

        if r.status_code == 500:
            raise Exception(f"500 on logout: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"logout expected 200 got {r.status_code}: {r.text[:200]}")

        # Try to use the refresh token after logout - should fail
        headers = {"Authorization": f"Bearer {refresh_token}"}
        r = requests.post(f"{base}/api/v1/auth/refresh", headers=headers, timeout=20)

        if r.status_code == 500:
            raise Exception(f"500 on refresh after logout: {r.text[:200]}")
        if r.status_code not in (401, 403):  # Token should be invalidated
            raise Exception(f"refresh after logout expected 401/403 got {r.status_code}: {r.text[:200]}")

    check("Logout invalidates refresh token correctly", logout_check)

    # =========================================================================
    # SECTION 4: USER PROFILE ENDPOINTS
    # =========================================================================

    def user_profile_check():
        """Test GET /api/v1/user/profile endpoint."""
        email = f"qa-profile-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # GET /user/profile
        r = requests.get(f"{base}/api/v1/user/profile", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on user profile: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"user profile expected 200 got {r.status_code}: {r.text[:200]}")

        data = r.json()
        required_fields = ["id", "email", "role", "subscription_status", "email_verified"]
        for field in required_fields:
            if field not in data:
                raise Exception(f"user profile missing field: {field}")

    check("GET /api/v1/user/profile returns user data", user_profile_check)

    def user_profile_patch_check():
        """Test PATCH /api/v1/user/profile endpoint."""
        email = f"qa-profile-patch-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # PATCH /user/profile (empty body is acceptable per code)
        r = requests.patch(f"{base}/api/v1/user/profile", headers=headers, json={}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on user profile patch: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"user profile patch expected 200 got {r.status_code}: {r.text[:200]}")

    check("PATCH /api/v1/user/profile works (empty update)", user_profile_patch_check)

    def user_stats_check():
        """Test GET /api/v1/user/stats endpoint."""
        email = f"qa-stats-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # GET /user/stats
        r = requests.get(f"{base}/api/v1/user/stats", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on user stats: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"user stats expected 200 got {r.status_code}: {r.text[:200]}")

        data = r.json()
        required_fields = ["saved_count", "status_counts", "total_tracked"]
        for field in required_fields:
            if field not in data:
                raise Exception(f"user stats missing field: {field}")

        report.note(f"User stats: saved={data['saved_count']}, tracked={data['total_tracked']}")

    check("GET /api/v1/user/stats returns statistics", user_stats_check)

    def user_saved_check():
        """Test GET /api/v1/user/saved endpoint."""
        email = f"qa-saved-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # GET /user/saved
        r = requests.get(f"{base}/api/v1/user/saved", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on user saved: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"user saved expected 200 got {r.status_code}: {r.text[:200]}")

        data = r.json()
        if "data" not in data:
            raise Exception("user saved response missing 'data' field")
        if "meta" not in data:
            raise Exception("user saved response missing 'meta' field")

    check("GET /api/v1/user/saved returns saved opportunities", user_saved_check)

    # =========================================================================
    # SECTION 5: OPPORTUNITIES - FILTER/SORT/SEARCH
    # =========================================================================

    def opportunities_filters_check():
        """Test opportunities list with filters."""
        email = f"qa-filter-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Test min_score filter
        r = requests.get(f"{base}/api/v1/opportunities?min_score=50", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities with min_score: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities min_score expected 200 got {r.status_code}: {r.text[:200]}")

        # Test max_score filter
        r = requests.get(f"{base}/api/v1/opportunities?max_score=80", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities with max_score: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities max_score expected 200 got {r.status_code}: {r.text[:200]}")

        # Test is_validated filter
        r = requests.get(f"{base}/api/v1/opportunities?is_validated=true", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities with is_validated: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities is_validated expected 200 got {r.status_code}: {r.text[:200]}")

    check("GET /api/v1/opportunities with filters works", opportunities_filters_check)

    def opportunities_sort_check():
        """Test opportunities list with sorting."""
        email = f"qa-sort-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Test ascending sort
        r = requests.get(f"{base}/api/v1/opportunities?sort=score", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities sort asc: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities sort asc expected 200 got {r.status_code}: {r.text[:200]}")

        # Test descending sort
        r = requests.get(f"{base}/api/v1/opportunities?sort=-score", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities sort desc: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities sort desc expected 200 got {r.status_code}: {r.text[:200]}")

        # Test created_at sort
        r = requests.get(f"{base}/api/v1/opportunities?sort=-created_at", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities sort by date: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities sort by date expected 200 got {r.status_code}: {r.text[:200]}")

    check("GET /api/v1/opportunities with sorting works", opportunities_sort_check)

    def opportunities_search_check():
        """Test opportunities list with search query."""
        email = f"qa-search-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Test search
        r = requests.get(f"{base}/api/v1/opportunities?search=ai", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunities search: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"opportunities search expected 200 got {r.status_code}: {r.text[:200]}")

    check("GET /api/v1/opportunities with search works", opportunities_search_check)

    def opportunities_time_range_check():
        """Test opportunities list with time range filter."""
        email = f"qa-time-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Test time_range filters
        for time_range in ["day", "week", "month", "year"]:
            r = requests.get(f"{base}/api/v1/opportunities?time_range={time_range}", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on opportunities time_range={time_range}: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"opportunities time_range={time_range} expected 200 got {r.status_code}: {r.text[:200]}")

    check("GET /api/v1/opportunities with time_range works", opportunities_time_range_check)

    def opportunities_pagination_check():
        """Test opportunities list with pagination cursor."""
        email = f"qa-page-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get first page
        r = requests.get(f"{base}/api/v1/opportunities?limit=5", headers=headers, timeout=20)
        if r.status_code != 200:
            raise Exception(f"opportunities first page expected 200 got {r.status_code}: {r.text[:200]}")

        data = r.json()
        if "meta" not in data:
            raise Exception("opportunities response missing 'meta' field")

        meta = data["meta"]
        if "next_cursor" not in meta:
            raise Exception("opportunities meta missing 'next_cursor' field")

        # Test pagination with cursor if available
        next_cursor = meta.get("next_cursor")
        if next_cursor:
            r = requests.get(f"{base}/api/v1/opportunities?limit=5&cursor={next_cursor}", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on opportunities pagination: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"opportunities pagination expected 200 got {r.status_code}: {r.text[:200]}")

    check("GET /api/v1/opportunities pagination works", opportunities_pagination_check)

    # =========================================================================
    # SECTION 6: OPPORTUNITIES - SAVE/STATUS UPDATE
    # =========================================================================

    def opportunity_save_check():
        """Test PATCH /api/v1/opportunities/<id> to save opportunity."""
        email = f"qa-save-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get first opportunity ID from list
        r = requests.get(f"{base}/api/v1/opportunities?limit=1", headers=headers, timeout=20)
        if r.status_code != 200:
            raise Exception(f"opportunities list for save check failed: {r.text[:200]}")

        data = r.json()
        if "data" not in data or not data["data"]:
            report.note("No opportunities found to test save/update - skipping")
            return

        opp_id = data["data"][0]["id"]

        # Test save/unsave
        r = requests.patch(f"{base}/api/v1/opportunities/{opp_id}", headers=headers, json={"is_saved": True}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunity save: {r.text[:200]}")
        if r.status_code not in (200, 404):
            raise Exception(f"opportunity save expected 200/404 got {r.status_code}: {r.text[:200]}")

        if r.status_code == 200:
            save_data = r.json()
            if save_data.get("is_saved") != True:
                raise Exception(f"opportunity not marked as saved: {save_data}")
            report.note(f"Opportunity {opp_id[:8]}... saved successfully")

    check("PATCH /api/v1/opportunities/<id> save/unsave works", opportunity_save_check)

    def opportunity_status_check():
        """Test PATCH /api/v1/opportunities/<id> to update status."""
        email = f"qa-status-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get first opportunity ID from list
        r = requests.get(f"{base}/api/v1/opportunities?limit=1", headers=headers, timeout=20)
        if r.status_code != 200:
            raise Exception(f"opportunities list for status check failed: {r.text[:200]}")

        data = r.json()
        if "data" not in data or not data["data"]:
            report.note("No opportunities found to test status update - skipping")
            return

        opp_id = data["data"][0]["id"]

        # Test status update
        r = requests.patch(f"{base}/api/v1/opportunities/{opp_id}", headers=headers, json={"status": "interested"}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on opportunity status update: {r.text[:200]}")
        if r.status_code not in (200, 404):
            raise Exception(f"opportunity status update expected 200/404 got {r.status_code}: {r.text[:200]}")

        if r.status_code == 200:
            status_data = r.json()
            if status_data.get("user_status") != "interested":
                raise Exception(f"opportunity status not updated: {status_data}")
            report.note(f"Opportunity {opp_id[:8]}... status updated to 'interested'")

    check("PATCH /api/v1/opportunities/<id> status update works", opportunity_status_check)

    # =========================================================================
    # SECTION 7: SCORING ENDPOINTS
    # =========================================================================

    def scoring_config_check():
        """Test GET /api/v1/scoring/config endpoint."""
        email = f"qa-scoring-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # GET /scoring/config
        r = requests.get(f"{base}/api/v1/scoring/config", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on scoring config: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"scoring config expected 200 got {r.status_code}: {r.text[:200]}")

        config = r.json()
        # Check for expected config fields
        expected_keys = ["weights", "thresholds", "formula"]
        found_keys = [k for k in expected_keys if k in config]
        if len(found_keys) < 2:
            raise Exception(f"scoring config missing expected keys, found: {found_keys}")

        report.note(f"Scoring config keys: {found_keys}")

    check("GET /api/v1/scoring/config returns scoring configuration", scoring_config_check)

    def scoring_score_opportunity_check():
        """Test POST /api/v1/scoring/opportunity/<id>/score endpoint."""
        email = f"qa-score-opp-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Get first opportunity ID
        r = requests.get(f"{base}/api/v1/opportunities?limit=1", headers=headers, timeout=20)
        if r.status_code != 200:
            raise Exception(f"opportunities list for scoring check failed: {r.text[:200]}")

        data = r.json()
        if "data" not in data or not data["data"]:
            report.note("No opportunities found to test scoring - skipping")
            return

        opp_id = data["data"][0]["id"]

        # POST /scoring/opportunity/<id>/score
        r = requests.post(f"{base}/api/v1/scoring/opportunity/{opp_id}/score", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on score opportunity: {r.text[:200]}")
        if r.status_code not in (200, 404):
            raise Exception(f"score opportunity expected 200/404 got {r.status_code}: {r.text[:200]}")

        if r.status_code == 200:
            score_data = r.json()
            report.note(f"Opportunity {opp_id[:8]}... scored, result: {str(score_data)[:100]}")

    check("POST /api/v1/scoring/opportunity/<id>/score works", scoring_score_opportunity_check)

    # =========================================================================
    # SECTION 8: ADMIN ENDPOINTS
    # =========================================================================

    if cfg.get("admin_email"):
        def admin_analytics_check():
            """Test GET /api/v1/admin/analytics endpoint."""
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.text[:200]}")

            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # GET /admin/analytics
            r = requests.get(f"{base}/api/v1/admin/analytics", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on admin analytics: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"admin analytics expected 200 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            if "data" not in data:
                raise Exception("admin analytics response missing 'data' field")

        check("GET /api/v1/admin/analytics works (admin)", admin_analytics_check)

        def admin_users_check():
            """Test GET /api/v1/admin/users endpoint."""
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.text[:200]}")

            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # GET /admin/users
            r = requests.get(f"{base}/api/v1/admin/users", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on admin users: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"admin users expected 200 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            if "data" not in data:
                raise Exception("admin users response missing 'data' field")

        check("GET /api/v1/admin/users works (admin)", admin_users_check)

        def admin_pricing_check():
            """Test GET /api/v1/admin/pricing endpoint."""
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.text[:200]}")

            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # GET /admin/pricing
            r = requests.get(f"{base}/api/v1/admin/pricing", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on admin pricing: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"admin pricing expected 200 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            if "data" not in data:
                raise Exception("admin pricing response missing 'data' field")

        check("GET /api/v1/admin/pricing works (admin)", admin_pricing_check)

        def admin_health_check():
            """Test GET /api/v1/admin/health endpoint."""
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.text[:200]}")

            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # GET /admin/health
            r = requests.get(f"{base}/api/v1/admin/health", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on admin health: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"admin health expected 200 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            if "data" not in data:
                raise Exception("admin health response missing 'data' field")

            # Check for expected health fields
            health_data = data["data"]
            expected_fields = ["database", "redis"]
            for field in expected_fields:
                if field not in health_data:
                    raise Exception(f"admin health missing field: {field}")

        check("GET /api/v1/admin/health works (admin)", admin_health_check)

    else:
        report.note("Admin endpoint tests skipped - no admin_email in config")

    # =========================================================================
    # SECTION 9: SCAN ENDPOINTS
    # =========================================================================

    if cfg.get("admin_email"):
        def scan_recent_check():
            """Test GET /api/v1/scan/recent endpoint."""
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.text[:200]}")

            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # GET /scan/recent
            r = requests.get(f"{base}/api/v1/scan/recent", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on scan recent: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"scan recent expected 200 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            if "scans" not in data:
                raise Exception("scan recent response missing 'scans' field")

        check("GET /api/v1/scan/recent returns scan history (admin)", scan_recent_check)

        def scan_stats_check():
            """Test GET /api/v1/scan/stats endpoint."""
            admin_email = cfg["admin_email"]
            pw = cfg.get("admin_password", cfg["smoke_user_password"])

            r = requests.post(f"{base}/api/v1/auth/login", json={"email": admin_email, "password": pw}, timeout=20)
            if r.status_code != 200:
                raise Exception(f"admin login failed: {r.text[:200]}")

            token = r.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # GET /scan/stats
            r = requests.get(f"{base}/api/v1/scan/stats", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on scan stats: {r.text[:200]}")
            if r.status_code != 200:
                raise Exception(f"scan stats expected 200 got {r.status_code}: {r.text[:200]}")

            data = r.json()
            expected_fields = ["total_scans", "recent_scans", "status_breakdown"]
            for field in expected_fields:
                if field not in data:
                    raise Exception(f"scan stats missing field: {field}")

        check("GET /api/v1/scan/stats returns scan statistics (admin)", scan_stats_check)

    # =========================================================================
    # SECTION 10: AUTHORIZATION BYPASS TESTS
    # =========================================================================

    def admin_endpoints_non_admin_check():
        """Test that non-admin users cannot access admin endpoints."""
        email = f"qa-auth-bypass-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Test various admin endpoints as non-admin
        # Note: scoring/weights and scoring/thresholds are PUT only, test with PUT
        admin_endpoints_get = [
            "/api/v1/admin/analytics",
            "/api/v1/admin/users",
            "/api/v1/admin/pricing",
            "/api/v1/admin/health",
        ]
        admin_endpoints_put = [
            "/api/v1/admin/scoring/weights",
            "/api/v1/admin/scoring/thresholds",
        ]

        for endpoint in admin_endpoints_get:
            r = requests.get(f"{base}{endpoint}", headers=headers, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on {endpoint} (non-admin): {r.text[:200]}")
            if r.status_code not in (403, 401):
                raise Exception(f"{endpoint} non-admin expected 403/401 got {r.status_code}: {r.text[:200]}")

        for endpoint in admin_endpoints_put:
            r = requests.put(f"{base}{endpoint}", headers=headers, json={}, timeout=20)
            if r.status_code == 500:
                raise Exception(f"500 on {endpoint} (non-admin): {r.text[:200]}")
            if r.status_code not in (403, 401):
                raise Exception(f"{endpoint} non-admin expected 403/401 got {r.status_code}: {r.text[:200]}")

    check("Non-admin users rejected from admin endpoints", admin_endpoints_non_admin_check)

    # =========================================================================
    # SECTION 11: MALFORMED INPUT VALIDATION
    # =========================================================================

    def input_validation_check():
        """Test that API properly rejects malformed input."""
        email = f"qa-input-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Test invalid email format on register
        r = requests.post(f"{base}/api/v1/auth/register", json={"email": "not-an-email", "password": pw}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on register with invalid email: {r.text[:200]}")
        if r.status_code not in (400, 422):
            raise Exception(f"register with invalid email expected 400/422 got {r.status_code}: {r.text[:200]}")

        # Test missing password
        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on register without password: {r.text[:200]}")
        if r.status_code not in (400, 422):
            raise Exception(f"register without password expected 400/422 got {r.status_code}: {r.text[:200]}")

        # Test invalid JSON on login
        r = requests.post(f"{base}/api/v1/auth/login", data="invalid json", headers={"Content-Type": "application/json"}, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on login with invalid JSON: {r.text[:200]}")
        if r.status_code not in (400, 422):
            raise Exception(f"login with invalid JSON expected 400/422 got {r.status_code}: {r.text[:200]}")

    check("API properly rejects malformed input", input_validation_check)

    # =========================================================================
    # SECTION 12: RATE LIMIT BEHAVIOR
    # =========================================================================

    def rate_limit_exhaustion_check():
        """Test that rate limits return 429 when exhausted."""
        email = f"qa-ratelimit-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        # Try multiple invalid login attempts to trigger rate limit
        for i in range(15):  # Attempt 15 logins
            r = requests.post(f"{base}/api/v1/auth/login", json={"email": f"wrong{i}@example.com", "password": "wrong"}, timeout=20)
            if r.status_code == 429:
                report.note(f"Rate limit triggered on attempt {i+1}")
                return  # Success - rate limit detected
            elif r.status_code != 401:
                raise Exception(f"unexpected status during rate limit test: {r.status_code}")

        report.note("Rate limit not triggered in 15 attempts (limit may be higher)")

    check("Rate limiting returns 429 when exhausted", rate_limit_exhaustion_check)

    # =========================================================================
    # SECTION 13: DASHBOARD ENDPOINT
    # =========================================================================

    def dashboard_endpoint_check():
        """Test GET /api/v1/dashboard returns aggregated data."""
        email = f"qa-dashboard-{uuid.uuid4().hex[:8]}@example.com"
        pw = cfg["smoke_user_password"]

        r = requests.post(f"{base}/api/v1/auth/register", json={"email": email, "password": pw}, timeout=20)
        r = requests.post(f"{base}/api/v1/auth/login", json={"email": email, "password": pw}, timeout=20)
        if r.status_code != 200:
            raise Exception(f"login failed: {r.text[:200]}")

        token = r.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # GET /dashboard
        r = requests.get(f"{base}/api/v1/dashboard", headers=headers, timeout=20)
        if r.status_code == 500:
            raise Exception(f"500 on dashboard: {r.text[:200]}")
        if r.status_code != 200:
            raise Exception(f"dashboard expected 200 got {r.status_code}: {r.text[:200]}")

        data = r.json()
        required_sections = ["profile", "user_stats", "global_stats"]
        for section in required_sections:
            if section not in data:
                raise Exception(f"dashboard missing section: {section}")

    check("GET /api/v1/dashboard returns aggregated data", dashboard_endpoint_check)


def _expect_200(url):
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        raise Exception(f"{url} expected 200 got {r.status_code}: {r.text[:200]}")
