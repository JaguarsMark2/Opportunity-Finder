import os, sys, time, uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE = os.getenv("APP_URL", "http://localhost:5173")

def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=opts)
driver.set_page_load_timeout(30)

try:
    driver.get(BASE)
    time.sleep(1)

    # Very basic: page must load and contain something app-like
    if "Opportunity" not in driver.page_source and "Login" not in driver.page_source and "Sign" not in driver.page_source:
        fail("Homepage loaded but expected login/signup content not found")

    print("PASS: Homepage loads")

finally:
    driver.quit()
