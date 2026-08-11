from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

import time


# ==========================================
# SETTINGS
# ==========================================

JOB_TITLE = "Python Developer"
LOCATION = "Pakistan"


SEARCH_URL = (
    "https://www.linkedin.com/jobs/search/"
    f"?keywords={JOB_TITLE.replace(' ', '%20')}"
    f"&location={LOCATION.replace(' ', '%20')}"
)


# ==========================================
# CHROME SETUP
# ==========================================

options = Options()

options.add_argument("--start-maximized")

# IMPORTANT:
# Do NOT use detach=True for this test.


# ==========================================
# START BROWSER
# ==========================================

print("Starting Chrome...")

driver = webdriver.Chrome(
    options=options
)

print("Chrome started successfully.")


# ==========================================
# OPEN LINKEDIN
# ==========================================

print("\nOpening LinkedIn Jobs...")

driver.get(SEARCH_URL)

print("LinkedIn Jobs opened.")

time.sleep(7)


# ==========================================
# MANUAL LOGIN
# ==========================================

print("\n----------------------------------------")
print("If LinkedIn asks for login,")
print("please login manually in Chrome.")
print("----------------------------------------")

input(
    "\nWhen the JOB SEARCH PAGE is visible, "
    "press ENTER here..."
)


# ==========================================
# CHECK BROWSER SESSION
# ==========================================

try:

    print("\nCurrent URL:")
    print(driver.current_url)

    print("\nPage title:")
    print(driver.title)

except WebDriverException as error:

    print("\n❌ Browser session was lost.")

    print(error)

    driver.quit()

    raise SystemExit


# ==========================================
# TEST SELECTORS
# ==========================================

selectors = [

    "li.jobs-search-results__list-item",

    "ul.jobs-search__results-list > li",

    "div.job-card-container",

    "div.base-card",

    "a[href*='/jobs/view/']"

]


print("\n========================================")
print("CHECKING LINKEDIN ELEMENTS")
print("========================================")


for selector in selectors:

    try:

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        print(
            f"{selector}"
            f"  -->  {len(elements)} found"
        )

    except WebDriverException:

        print(
            f"{selector}"
            "  -->  Browser session lost"
        )

        break


# ==========================================
# FIND JOB LINKS
# ==========================================

try:

    job_links = driver.find_elements(
        By.CSS_SELECTOR,
        "a[href*='/jobs/view/']"
    )

except WebDriverException as error:

    print(
        "\n❌ Selenium lost the browser session."
    )

    print(error)

    driver.quit()

    raise SystemExit


print(
    f"\nJob links found: {len(job_links)}"
)


# ==========================================
# DISPLAY JOB LINKS
# ==========================================

seen_links = set()


for index, link in enumerate(
    job_links,
    start=1
):

    try:

        href = link.get_attribute(
            "href"
        )

        title = link.text.strip()


        if not href:
            continue


        if href in seen_links:
            continue


        seen_links.add(href)


        print(
            f"\n{index}. {title}"
        )

        print(
            href
        )


    except Exception:

        continue


# ==========================================
# FINISH
# ==========================================

print("\n========================================")
print("JOB SEARCH TEST COMPLETED")
print("========================================")


input(
    "\nPress ENTER to close Chrome..."
)


driver.quit()