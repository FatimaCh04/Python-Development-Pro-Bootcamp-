import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time


# ============================================================
# SETTINGS
# ============================================================

ZILLOW_URL = "https://appbrewery.github.io/Zillow-Clone/"

# IMPORTANT:
# Yahan apna Google Form URL paste karo.
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfvU7Fv7ELuBhN8bK_X0ha8SQeVa_HsS9IoaGuL7eXjF--Xyw/viewform?usp=publish-editor"


# ============================================================
# HEADERS
# ============================================================

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


# ============================================================
# GET PROPERTY WEBSITE
# ============================================================

print("\n🏠 Getting property data...")

response = requests.get(
    ZILLOW_URL,
    headers=headers,
    timeout=20
)

response.raise_for_status()


# ============================================================
# BEAUTIFULSOUP
# ============================================================

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ============================================================
# GET ADDRESSES
# ============================================================

address_elements = soup.select(
    ".StyledPropertyCardDataWrapper address"
)

addresses = []

for address in address_elements:

    clean_address = (
        address.get_text(
            strip=True
        )
        .replace(" | ", " ")
    )

    addresses.append(
        clean_address
    )


# ============================================================
# GET PRICES
# ============================================================

price_elements = soup.select(
    'span[data-test="property-card-price"]'
)

prices = []

for price in price_elements:

    clean_price = (
        price.get_text(
            strip=True
        )
        .split("+")[0]
        .strip()
    )

    prices.append(
        clean_price
    )


# ============================================================
# GET LINKS
# ============================================================

link_elements = soup.select(
    ".StyledPropertyCardDataWrapper a"
)

links = []

for link in link_elements:

    href = link.get("href")

    if href:

        links.append(
            href
        )


# ============================================================
# MAKE SURE ALL DATA HAS SAME LENGTH
# ============================================================

number_of_properties = min(
    len(addresses),
    len(prices),
    len(links)
)


print(
    f"\nFound {number_of_properties} properties."
)


if number_of_properties == 0:

    print(
        "\n❌ No properties found."
    )

    print(
        "The website HTML/selectors may have changed."
    )

    exit()


# ============================================================
# STORE PROPERTY DATA
# ============================================================

properties = []

for i in range(
    number_of_properties
):

    property_data = {

        "address": addresses[i],

        "price": prices[i],

        "link": links[i]

    }

    properties.append(
        property_data
    )


# ============================================================
# DISPLAY DATA
# ============================================================

print(
    "\n========== PROPERTY DATA ==========\n"
)


for index, property_data in enumerate(
    properties,
    start=1
):

    print(
        f"{index}. "
        f"{property_data['address']}"
    )

    print(
        f"   Price: "
        f"{property_data['price']}"
    )

    print(
        f"   Link: "
        f"{property_data['link']}"
    )

    print(
        "-" * 60
    )


# ============================================================
# CHECK GOOGLE FORM URL
# ============================================================

if (
    FORM_URL
    == "PASTE_YOUR_GOOGLE_FORM_URL_HERE"
):

    print(
        "\n❌ ERROR:"
    )

    print(
        "Please put your Google Form URL "
        "inside FORM_URL."
    )

    exit()


# ============================================================
# SELENIUM SETUP
# ============================================================

print(
    "\n🌐 Opening Google Form..."
)


chrome_options = Options()

chrome_options.add_experimental_option(
    "detach",
    True
)


driver = webdriver.Chrome(
    options=chrome_options
)


wait = WebDriverWait(
    driver,
    15
)


# ============================================================
# OPEN GOOGLE FORM
# ============================================================

driver.get(
    FORM_URL
)


time.sleep(3)


print(
    "Google Form opened."
)


# ============================================================
# ENTER PROPERTY DATA
# ============================================================

for index, property_data in enumerate(
    properties,
    start=1
):

    print(
        f"\n📝 Processing property "
        f"{index}/{number_of_properties}"
    )

    print(
        property_data["address"]
    )


    # --------------------------------------------------------
    # WAIT FOR VISIBLE INPUTS
    # --------------------------------------------------------

    try:

        wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "input[type='text']"
                )
            )
        )

    except Exception:

        print(
            "❌ Could not find form inputs."
        )

        break


    # --------------------------------------------------------
    # GET ONLY VISIBLE INPUTS
    # --------------------------------------------------------

    inputs = []

    all_inputs = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='text']"
    )


    for input_element in all_inputs:

        if (
            input_element.is_displayed()
            and input_element.is_enabled()
        ):

            inputs.append(
                input_element
            )


    print(
        f"Visible text inputs found: "
        f"{len(inputs)}"
    )


    # --------------------------------------------------------
    # CHECK INPUT COUNT
    # --------------------------------------------------------

    if len(inputs) < 3:

        print(
            "\n❌ Less than 3 visible inputs found."
        )

        print(
            "Your Google Form should have exactly "
            "these text questions:"
        )

        print(
            "1. Address"
        )

        print(
            "2. Price"
        )

        print(
            "3. Link"
        )

        break


    # --------------------------------------------------------
    # CLEAR OLD DATA
    # --------------------------------------------------------

    for input_element in inputs[:3]:

        input_element.clear()


    # --------------------------------------------------------
    # ENTER ADDRESS
    # --------------------------------------------------------

    inputs[0].send_keys(
        property_data["address"]
    )


    # --------------------------------------------------------
    # ENTER PRICE
    # --------------------------------------------------------

    inputs[1].send_keys(
        property_data["price"]
    )


    # --------------------------------------------------------
    # ENTER LINK
    # --------------------------------------------------------

    inputs[2].send_keys(
        property_data["link"]
    )


    print(
        "✅ Address entered"
    )

    print(
        "✅ Price entered"
    )

    print(
        "✅ Link entered"
    )


    # --------------------------------------------------------
    # FIND SUBMIT BUTTON
    # --------------------------------------------------------

    submit_buttons = driver.find_elements(
        By.XPATH,
        "//span[contains(text(), 'Submit')]"
    )


    if not submit_buttons:

        submit_buttons = driver.find_elements(
            By.XPATH,
            "//div[@role='button']"
        )


    # --------------------------------------------------------
    # CLICK SUBMIT
    # --------------------------------------------------------

    submitted = False


    for button in submit_buttons:

        try:

            if (
                button.is_displayed()
                and button.is_enabled()
            ):

                button.click()

                submitted = True

                break

        except Exception:

            continue


    if not submitted:

        print(
            "⚠️ Submit button not found."
        )

        print(
            "Please check your Google Form."
        )

        break


    print(
        "✅ Form submitted!"
    )


    # --------------------------------------------------------
    # WAIT AFTER SUBMISSION
    # --------------------------------------------------------

    time.sleep(2)


    # --------------------------------------------------------
    # RETURN TO FORM
    # --------------------------------------------------------

    try:

        back_to_form = driver.find_element(
            By.XPATH,
            "//a[contains(text(), 'Submit another response')]"
        )

        back_to_form.click()

    except Exception:

        driver.get(
            FORM_URL
        )


    time.sleep(2)


# ============================================================
# FINISHED
# ============================================================

print(
    "\n=========================================="
)

print(
    "🎉 DAY 53 AUTOMATED DATA ENTRY COMPLETE!"
)

print(
    "=========================================="
)


input(
    "\nPress ENTER to close the browser..."
)


driver.quit()