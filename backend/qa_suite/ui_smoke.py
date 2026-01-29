"""UI smoke tests for Opportunity Finder frontend.

Comprehensive UI tests including:
- Basic page loads and navigation
- Form presence and structure checks
- Signup/login flow verification
- Dashboard route guard checks
- UX dead-end detection (e.g., "check your email" without escape path)
"""

import time
import uuid
from selenium_common import make_driver, click_first_text, find_inputs, list_texts


def run_ui_checks(cfg, report):
    driver = make_driver(cfg["headless"], cfg["timeouts"]["page_load"])
    try:
        f = cfg["frontend_url"].rstrip("/")

        # Warn if frontend appears to be down
        try:
            driver.set_page_load_timeout(5)
            driver.get(f)
            # If we get here without exception, server is running
            report.pass_("Frontend server is running")
        except Exception as e:
            report.fail("Frontend server is running", f"Cannot connect to {f}: {str(e)[:100]}")
            return  # Cannot continue UI tests if frontend is down

        # Reset to configured timeout
        driver.set_page_load_timeout(cfg["timeouts"]["page_load"])
        driver.get(f)
        time.sleep(cfg["timeouts"]["sleep_short"])
        report.pass_("UI homepage loads")

        buttons, links = list_texts(driver)
        report.note(f"Homepage links={links}")
        report.note(f"Homepage buttons={buttons}")

        if any(t in links for t in cfg["signin_link_texts"]):
            report.pass_("UI has Sign In link")
        else:
            report.fail("UI has Sign In link", f"missing any of {cfg['signin_link_texts']}")

        if any(t in links for t in cfg["signup_link_texts"]):
            report.pass_("UI has Signup/Get Started link")
        else:
            report.fail("UI has Signup/Get Started link", f"missing any of {cfg['signup_link_texts']}")

        # Sign-in page checks
        clicked = click_first_text(driver, cfg["signin_link_texts"])
        if not clicked:
            report.fail("UI Sign In click", "could not click sign-in link")
            return
        time.sleep(cfg["timeouts"]["sleep_short"])
        signin_url = driver.current_url
        emails, passwords, submits = find_inputs(driver)
        if emails and passwords and submits:
            report.pass_("UI Sign In form has email/password/submit")
        else:
            report.fail(
                "UI Sign In form has email/password/submit",
                f"email={len(emails)} pw={len(passwords)} submit={len(submits)}",
            )

        # Signup page checks
        driver.get(f)
        time.sleep(cfg["timeouts"]["sleep_short"])
        clicked = click_first_text(driver, cfg["signup_link_texts"])
        if not clicked:
            report.fail("UI Signup click", "could not click signup link")
            return
        time.sleep(cfg["timeouts"]["sleep_short"])
        signup_url = driver.current_url
        emails, passwords, submits = find_inputs(driver)
        if emails and passwords and submits:
            report.pass_("UI Signup form has email/password/submit")
        else:
            report.fail(
                "UI Signup form has email/password/submit",
                f"email={len(emails)} pw={len(passwords)} submit={len(submits)}",
            )
            return

        # Attempt signup
        email = f"qa-ui-{uuid.uuid4().hex[:8]}@example.com"
        emails[0].send_keys(email)
        passwords[0].send_keys(cfg["smoke_user_password"])
        if len(passwords) > 1:
            passwords[1].send_keys(cfg["smoke_user_password"])
        submits[0].click()
        time.sleep(cfg["timeouts"]["sleep_medium"])

        page = driver.page_source.lower()
        page_text = driver.page_source
        current_url = driver.current_url

        # Check for success/verify message
        if ("check your email" in page) or ("verify" in page) or ("successful" in page):
            report.pass_("UI Signup shows success/verify message")
        else:
            report.fail("UI Signup shows success/verify message", "could not detect success/verify text")

        # UX dead-end check: look for login/back option
        if ("sign in" in page) or ("login" in page) or ("log in" in page):
            report.pass_("UI post-signup offers login")
        else:
            # Check for visible buttons/links that might lead back
            buttons, links = list_texts(driver)
            escape_options = [t for t in links + buttons if any(s in t.lower() for s in ["sign in", "login", "log in", "back", "home"])]
            if escape_options:
                report.pass_("UI post-signup offers escape path", f"found: {escape_options}")
            else:
                report.fail("UI post-signup offers escape path", f"no login/back option detected (user stuck on verify page). Page: {current_url}")

        # Attempt login
        if not click_first_text(driver, cfg["signin_link_texts"]):
            driver.get(f)
            time.sleep(cfg["timeouts"]["sleep_short"])
            click_first_text(driver, cfg["signin_link_texts"])
        time.sleep(cfg["timeouts"]["sleep_short"])
        emails, passwords, submits = find_inputs(driver)
        if not (emails and passwords and submits):
            report.fail("UI login attempt possible", "login form fields not found after navigation")
            return

        emails[0].clear()
        emails[0].send_keys(email)
        passwords[0].clear()
        passwords[0].send_keys(cfg["smoke_user_password"])
        submits[0].click()
        time.sleep(cfg["timeouts"]["sleep_medium"])

        url = driver.current_url.lower()
        bad = [s for s in cfg["expected_login_not_contains"] if s.lower() in url]
        if bad:
            report.fail("UI login redirect is acceptable", f"url={driver.current_url} contains {bad}")
        else:
            report.pass_("UI login redirect is acceptable")

        # Dashboard guard check: authenticated user should access dashboard
        report.note(f"Post-login URL: {driver.current_url}")

        # Check if /dashboard is accessible
        driver.get(f + "/dashboard")
        time.sleep(cfg["timeouts"]["sleep_short"])
        dashboard_accessible = "dashboard" in driver.current_url.lower()
        page = driver.page_source.lower()

        if dashboard_accessible or ("opportunities" in page or "welcome" in page or "dashboard" in page):
            report.pass_("UI /dashboard accessible when authenticated")
        else:
            report.fail("UI /dashboard accessible when authenticated", f"URL={driver.current_url}, page content suggests redirect/block")

        # Now check anonymous user cannot access dashboard
        driver.delete_all_cookies()
        driver.get(f + "/dashboard")
        time.sleep(cfg["timeouts"]["sleep_short"])

        page = driver.page_source.lower()
        current_url = driver.current_url.lower()

        # Should be redirected to login or shown auth error
        is_protected = (
            "sign in" in page or "login" in page or "log in" in page or
            "unauthorized" in page or "forbidden" in page or
            "/login" in current_url or "/signin" in current_url
        )

        if is_protected:
            report.pass_("UI /dashboard guarded when not authenticated")
        else:
            report.fail("UI /dashboard guarded when not authenticated", f"URL={driver.current_url} - page appears accessible without auth")

    finally:
        driver.quit()
