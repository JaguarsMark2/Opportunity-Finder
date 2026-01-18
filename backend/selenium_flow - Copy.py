import os, time, uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE = os.getenv("APP_URL", "http://localhost:5173")

issues = []

def die(msg: str) -> None:
    issues.append(msg)
    print("BUG:", msg)

def click_text(driver, text: str) -> None:
    els = driver.find_elements(By.XPATH, f"//*[normalize-space()='{text}']")
    if not els:
        die(f"Could not find element with text '{text}'")
    els[0].click()

def find_any_text(driver, *texts: str) -> bool:
    src = driver.page_source
    return any(t in src for t in texts)

def main() -> None:
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
        for label in ("Get Started Free", "Get Started", "Start Free Trial", "Sign Up", "Sign up"):
            try:
                click_text(driver, label)
                break
            except SystemExit:
                raise
            except Exception:
                pass
        else:
            die("Could not find a signup link (Get Started / Start Free Trial / Sign Up)")

        time.sleep(1)

        # Fill signup form
        email_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
        if not email_inputs:
            die("No email input found on signup form")
        email_inputs[0].send_keys(email)

        pw_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if len(pw_inputs) < 1:
            die("No password inputs found on signup form")
        pw_inputs[0].send_keys(password)
        if len(pw_inputs) > 1:
            pw_inputs[1].send_keys(password)

        # Submit
        btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if not btns:
            die("No submit button found on signup form")
        btns[0].click()

        time.sleep(2)

        # Bug check 1: should offer a way back to login
        if not find_any_text(driver, "Log in", "Login", "Back"):
            print("BUG: After signup, no 'Back to login' / 'Login' option detected")

        # Go back (what a user currently must do)
        driver.back()
        time.sleep(1)

        # Login
        email_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
        if not email_inputs:
            die("No email input found on login form")
        else:
            email_inputs[0].clear()
            email_inputs[0].send_keys(email)

        pw_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if not pw_inputs:
            die("No password input found on login form")
        else:
            pw_inputs[0].clear()
            pw_inputs[0].send_keys(password)

        btns = driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")
        if not btns:
            die("No submit button found on login form")
    else:
        btns[0].click()

        time.sleep(2)

        url = driver.current_url
        print("After login URL:", url)

        if "dashboard" in url.lower():
            print("BUG: Login redirects to dashboard by default")
        else:
            print("PASS: Login did not redirect to dashboard")

    finally:
        driver.quit()

    open('selenium_report.txt','w',encoding='utf-8').write('\n'.join(issues) + ('\n' if issues else ''))
    print('REPORT:', 'selenium_report.txt')

if __name__ == "__main__":
    main()
