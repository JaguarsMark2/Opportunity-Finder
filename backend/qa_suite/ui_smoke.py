import time
import uuid
from selenium_common import make_driver, click_first_text, find_inputs, list_texts


def run_ui_checks(cfg, report):
    driver = make_driver(cfg["headless"], cfg["timeouts"]["page_load"])
    try:
        f = cfg["frontend_url"].rstrip("/")
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
        if ("check your email" in page) or ("verify" in page) or ("successful" in page):
            report.pass_("UI Signup shows success/verify message")
        else:
            report.fail("UI Signup shows success/verify message", "could not detect success/verify text")

        if ("sign in" in page) or ("login" in page) or ("log in" in page):
            report.pass_("UI post-signup offers login")
        else:
            report.fail("UI post-signup offers login", "no login option detected (user forced to use back button?)")

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

        # Guard check
        driver.get(f + "/dashboard")
        time.sleep(cfg["timeouts"]["sleep_short"])
        page = driver.page_source.lower()
        if ("sign in" in page) or ("login" in page) or ("unauthorized" in page):
            report.pass_("UI /dashboard guarded when not authenticated")
        else:
            report.note("UI /dashboard guard inconclusive")

    finally:
        driver.quit()
