import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def make_driver(headless: bool, page_load_timeout: int):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(page_load_timeout)
    return driver


def click_first_text(driver, labels):
    for label in labels:
        try:
            els = driver.find_elements(By.XPATH, f"//*[normalize-space()='{label}']")
            if els:
                els[0].click()
                return label
        except Exception:
            pass
    return None


def find_inputs(driver):
    emails = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
    passwords = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
    submits = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    return emails, passwords, submits


def list_texts(driver):
    buttons = [b.text.strip() for b in driver.find_elements(By.TAG_NAME, "button") if b.text.strip()]
    links = [a.text.strip() for a in driver.find_elements(By.TAG_NAME, "a") if a.text.strip()]
    return buttons, links
