from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time


# ==========================================
# SETTINGS
# ==========================================

INSTAGRAM_URL = "https://www.instagram.com/"

TARGET_PROFILE = "instagram"


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

wait = WebDriverWait(
    driver,
    15
)


# ==========================================
# OPEN INSTAGRAM
# ==========================================

driver.get(
    INSTAGRAM_URL
)

print("Instagram opened.")

time.sleep(5)


# ==========================================
# MANUAL LOGIN
# ==========================================

print()
print("Please log in manually if required.")
print("Complete any verification/CAPTCHA manually.")

input(
    "\nPress ENTER after Instagram is ready..."
)


# ==========================================
# OPEN TARGET PROFILE
# ==========================================

profile_url = (
    f"https://www.instagram.com/"
    f"{TARGET_PROFILE}/"
)

driver.get(
    profile_url
)

time.sleep(5)


# ==========================================
# GET PROFILE INFORMATION
# ==========================================

print("\n========== PROFILE ==========\n")


try:

    profile_header = wait.until(
        EC.presence_of_element_located(
            (
                By.TAG_NAME,
                "header"
            )
        )
    )

    print(
        "Profile header found successfully."
    )

except Exception:

    print(
        "Could not find profile header."
    )


# ==========================================
# FIND BUTTONS
# ==========================================

try:

    buttons = driver.find_elements(
        By.TAG_NAME,
        "button"
    )

    print(
        f"\nVisible buttons: "
        f"{len(buttons)}"
    )


    for index, button in enumerate(
        buttons[:15],
        start=1
    ):

        try:

            text = button.text.strip()

            aria_label = button.get_attribute(
                "aria-label"
            )

            if text:

                print(
                    f"{index}. {text}"
                )

            elif aria_label:

                print(
                    f"{index}. {aria_label}"
                )

        except Exception:

            continue

except Exception:

    print(
        "Could not inspect buttons."
    )


# ==========================================
# PAGE TITLE
# ==========================================

print(
    "\nPage title:"
)

print(
    driver.title
)


# ==========================================
# CURRENT URL
# ==========================================

print(
    "\nCurrent URL:"
)

print(
    driver.current_url
)


# ==========================================
# FINISH
# ==========================================

print(
    "\nInstagram Selenium practice "
    "completed successfully."
)


input(
    "\nPress ENTER to close the browser..."
)


driver.quit()