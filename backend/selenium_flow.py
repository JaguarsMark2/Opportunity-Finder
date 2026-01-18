import os, time, uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE = os.getenv("APP_URL", "http://localhost:5173")

issues = []

def bug(msg: str) -> None:
    issues.append(msg)
    print("BUG:", msg)

def click_first_text(driver, labels):
    for label in labels:
        try:
            els = driver.find_elements(By.XPATH, f"//*[normalize-space()='{label}']")
            if els:
                els[0].click()
                return True
        except Exception:
            pass
    return False

def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)

    email = f"flow-{uuid.uuid4().hex[:8]}@example.com"
    password = "Test1234!"

    try:
        driver.get(BASE)
        time.sleep(1)

        # Go to signup
        ok = click_first_text(driver, ["Get Started Free", "Get Started", "Start Free Trial", "Sign Up", "Sign up"])
        if not ok:
            bug("Could not find a signup link (Get Started / Start Free Trial / Sign Up)")
            return

        time.sleep(1)

        # Signup form fields
        email_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
        if not email_inputs:
            bug("No email input found on signup form")
            return
        email_inputs[0].send_keys(email)

        pw_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(pw_inputs) < 1:
            bug("No password inputs found on signup form")
            return
        pw_inputs[0].send_keys(password)
        if len(pw_inputs) > 1:
            pw_inputs[1].send_keys(password)

        submit = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if not submit:
            bug("No submit button found on signup form")
            return
        submit[0].click()
        time.sleep(2)

        # Post-signup UX check
        page = driver.page_source
        if ("Log in" not in page) and ("Login" not in page) and ("Back" not in page):
            bug("After signup, no 'Back to login' / 'Login' option detected")

        # Go back to login (current workaround)
        driver.back()
        time.sleep(1)

        # Login form fields
        email_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
        if not email_inputs:
            bug("No email input found on login form")
        else:
            email_inputs[0].clear()
            email_inputs[0].send_keys(email)

        pw_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if not pw_inputs:
            bug("No password input found on login form")
        else:
            pw_inputs[0].clear()
            pw_inputs[0].send_keys(password)

        submit = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if not submit:
            bug("No submit button found on login form")
        else:
            submit[0].click()

        time.sleep(2)

        url = driver.current_url
        print("After login URL:", url)
        if "dashboard" in url.lower():
            bug("Login redirects to dashboard by default")

    finally:
        driver.quit()
        with open("selenium_report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(issues) + ("\n" if issues else ""))
        print("REPORT: selenium_report.txt")

if __name__ == "__main__":
    main()
