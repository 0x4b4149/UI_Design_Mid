"""Capture full-page screenshots for the midterm report.

Requires a local server on http://127.0.0.1:8000 and Selenium + Chrome.

    python scripts/capture_screens.py
"""

import base64
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def make_driver(width=1440, height=1600):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--hide-scrollbars")
    options.add_argument(f"--window-size={width},{height}")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--font-render-hinting=none")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(width, height)
    return driver


def wait_for_page(driver):
    time.sleep(0.6)
    try:
        driver.execute_async_script(
            "const done = arguments[0]; document.fonts.ready.then(() => done());"
        )
    except Exception:
        pass
    time.sleep(0.4)


def full_screenshot(driver, name):
    metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    content = metrics["contentSize"]
    width = max(1200, int(content["width"]))
    height = max(800, int(content["height"]))
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "mobile": False,
        },
    )
    time.sleep(0.25)
    data = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
    path = OUT / f"{name}.png"
    path.write_bytes(base64.b64decode(data["data"]))
    driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
    print(f"saved {path}")


def screenshot(driver, path, name, full=True):
    driver.get(BASE_URL + path)
    wait_for_page(driver)
    if full:
        full_screenshot(driver, name)
    else:
        driver.save_screenshot(str(OUT / f"{name}.png"))
        print(f"saved {name}.png")


def login(driver, username, password):
    driver.get(BASE_URL + "/accounts/login/")
    wait_for_page(driver)
    driver.find_element(By.ID, "id_username").send_keys(username)
    driver.find_element(By.ID, "id_password").send_keys(password)
    button = driver.find_element(By.CSS_SELECTOR, "form.auth-form button[type=submit]")
    driver.execute_script("arguments[0].click();", button)
    time.sleep(1.2)


def main():
    public_pages = [
        ("/", "01-home"),
        ("/locations/", "02-locations"),
        ("/locations/new-york-ny/", "03-location-detail"),
        ("/alerts/", "04-alerts"),
        ("/alerts/1/", "05-alert-detail"),
        ("/accounts/login/", "06-login"),
        ("/accounts/register/", "07-register"),
        ("/locations/?q=New+York&region=northeast&condition=partly_cloudy&temp_min=50&temp_max=70&alerts=1", "08-filter-results"),
    ]

    driver = make_driver()
    try:
        for path, name in public_pages:
            screenshot(driver, path, name)
        login(driver, "demo", "Demo1234!")
        screenshot(driver, "/dashboard/", "09-member-dashboard")
        screenshot(driver, "/?unit=c", "10-home-celsius")
    finally:
        driver.quit()

    admin = make_driver()
    try:
        login(admin, "admin", "Admin1234!")
        screenshot(admin, "/admin/", "11-django-admin")
        screenshot(admin, "/admin/forecast/location/", "12-admin-locations")
        screenshot(admin, "/admin/forecast/alert/", "13-admin-alerts")
        screenshot(admin, "/admin/forecast/currentconditions/", "14-admin-conditions")
        screenshot(admin, "/admin/auth/user/", "15-admin-members")
    finally:
        admin.quit()

    mobile = make_driver(width=390, height=900)
    try:
        screenshot(mobile, "/", "16-home-mobile", full=False)
        screenshot(mobile, "/locations/", "17-locations-mobile", full=False)
        login(mobile, "demo", "Demo1234!")
        screenshot(mobile, "/dashboard/", "18-dashboard-mobile", full=False)
    finally:
        mobile.quit()


if __name__ == "__main__":
    main()
