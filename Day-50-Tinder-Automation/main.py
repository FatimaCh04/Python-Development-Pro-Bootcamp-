from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import time


# ==========================================
# SETTINGS
# ==========================================

TINDER_URL = "https://tinder.com/"


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
# OPEN TINDER
# ==========================================

driver.get(TINDER_URL)

print("Tinder website opened.")

time.sleep(5)


# ==========================================
# MANUAL LOGIN
# ==========================================

print()
print("Please log in manually if required.")
print("Complete any verification or CAPTCHA manually.")

input(
    "\nPress ENTER after the website is ready..."
)


# ==========================================
# DEMONSTRATION LOOP
# ==========================================

print("\nStarting Selenium automation demo...")


for count in range(10):

    print(
        f"\nAutomation step {count + 1}"
    )


    # --------------------------------------
    # FIND AVAILABLE BUTTONS
    # --------------------------------------

    buttons = driver.find_elements(
        By.TAG_NAME,
        "button"
    )


    print(
        f"Buttons currently visible: "
        f"{len(buttons)}"
    )


    # --------------------------------------
    # DISPLAY BUTTON TEXT
    # --------------------------------------

    for index, button in enumerate(
        buttons[:10],
        start=1
    ):

        try:

            text = button.text.strip()

            aria_label = button.get_attribute(
                "aria-label"
            )

            if text:

                print(
                    f"{index}. Text: {text}"
                )

            elif aria_label:

                print(
                    f"{index}. "
                    f"ARIA label: {aria_label}"
                )

        except Exception:

            continue


    time.sleep(2)


# ==========================================
# FINISH
# ==========================================

print(
    "\n🍪 Selenium automation demonstration complete."
)


input(
    "\nPress ENTER to close the browser..."
)


driver.quit()