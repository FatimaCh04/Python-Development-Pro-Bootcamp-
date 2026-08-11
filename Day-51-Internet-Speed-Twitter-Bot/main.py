from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import time
import re


# ==========================================
# INTERNET PLAN SETTINGS
# ==========================================

PROMISED_DOWNLOAD = 50
PROMISED_UPLOAD = 10


# ==========================================
# CHROME SETUP
# ==========================================

options = Options()

options.add_experimental_option(
    "detach",
    True
)

driver = webdriver.Chrome(
    options=options
)


# ==========================================
# OPEN SPEEDTEST
# ==========================================

print("Opening Speedtest...")

driver.get(
    "https://www.speedtest.net/"
)

time.sleep(5)


# ==========================================
# ACCEPT COOKIES IF AVAILABLE
# ==========================================

try:

    buttons = driver.find_elements(
        By.TAG_NAME,
        "button"
    )

    for button in buttons:

        text = button.text.lower()

        if "accept" in text:

            button.click()

            break

except Exception:

    pass


# ==========================================
# START SPEED TEST
# ==========================================

try:

    start_button = driver.find_element(
        By.CSS_SELECTOR,
        "a.js-start-test"
    )

    start_button.click()

    print(
        "Speed test started..."
    )

except Exception:

    print(
        "Could not automatically start "
        "the speed test."
    )

    print(
        "Please start it manually."
    )


# ==========================================
# WAIT FOR TEST
# ==========================================

time.sleep(45)


# ==========================================
# GET DOWNLOAD SPEED
# ==========================================

download_speed = None

try:

    download_element = driver.find_element(
        By.CSS_SELECTOR,
        ".download-speed"
    )

    download_text = (
        download_element.text
    )

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        download_text
    )

    if numbers:

        download_speed = float(
            numbers[0]
        )

except Exception:

    pass


# ==========================================
# GET UPLOAD SPEED
# ==========================================

upload_speed = None

try:

    upload_element = driver.find_element(
        By.CSS_SELECTOR,
        ".upload-speed"
    )

    upload_text = (
        upload_element.text
    )

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        upload_text
    )

    if numbers:

        upload_speed = float(
            numbers[0]
        )

except Exception:

    pass


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n========== SPEED TEST ==========")

print(
    f"Promised Download: "
    f"{PROMISED_DOWNLOAD} Mbps"
)

print(
    f"Promised Upload: "
    f"{PROMISED_UPLOAD} Mbps"
)


if download_speed is not None:

    print(
        f"Actual Download: "
        f"{download_speed} Mbps"
    )

else:

    print(
        "Actual Download: "
        "Could not detect"
    )


if upload_speed is not None:

    print(
        f"Actual Upload: "
        f"{upload_speed} Mbps"
    )

else:

    print(
        "Actual Upload: "
        "Could not detect"
    )


# ==========================================
# CALCULATE DIFFERENCE
# ==========================================

download_difference = None

upload_difference = None


if download_speed is not None:

    download_difference = (
        PROMISED_DOWNLOAD
        - download_speed
    )


if upload_speed is not None:

    upload_difference = (
        PROMISED_UPLOAD
        - upload_speed
    )


# ==========================================
# CREATE COMPLAINT
# ==========================================

complaint = (
    "My internet provider is not delivering "
    "the promised internet speed.\n\n"
    f"Promised download speed: "
    f"{PROMISED_DOWNLOAD} Mbps\n"
    f"Actual download speed: "
    f"{download_speed if download_speed else 'N/A'} Mbps\n\n"
    f"Promised upload speed: "
    f"{PROMISED_UPLOAD} Mbps\n"
    f"Actual upload speed: "
    f"{upload_speed if upload_speed else 'N/A'} Mbps\n\n"
    "#InternetSpeed #ISP"
)


print(
    "\n========== COMPLAINT ==========\n"
)

print(complaint)


# ==========================================
# CHECK WHETHER COMPLAINT IS NEEDED
# ==========================================

needs_complaint = False


if (
    download_speed is not None
    and download_speed < PROMISED_DOWNLOAD
):

    needs_complaint = True


if (
    upload_speed is not None
    and upload_speed < PROMISED_UPLOAD
):

    needs_complaint = True


if needs_complaint:

    print(
        "\n⚠️ Your internet speed is "
        "below the promised speed."
    )

    print(
        "Complaint prepared for review."
    )

else:

    print(
        "\n✅ Internet speed meets "
        "the configured plan."
    )


# ==========================================
# FINISH
# ==========================================

input(
    "\nPress ENTER to close the browser..."
)


driver.quit()