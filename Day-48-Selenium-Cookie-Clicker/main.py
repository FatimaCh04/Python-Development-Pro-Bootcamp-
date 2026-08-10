from selenium import webdriver
from selenium.webdriver.common.by import By
import time


# ==========================================
# SETUP
# ==========================================

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

driver.get("https://orteil.dashnet.org/cookieclicker/")

time.sleep(5)


# ==========================================
# SELECT ENGLISH
# ==========================================

try:
    driver.find_element(By.ID, "langSelect-EN").click()
    time.sleep(3)
except Exception:
    pass


# ==========================================
# COOKIE
# ==========================================

cookie = driver.find_element(By.ID, "bigCookie")


# ==========================================
# GAME SETTINGS
# ==========================================

GAME_TIME = 5 * 60
CHECK_INTERVAL = 5

start_time = time.time()
next_check = time.time() + CHECK_INTERVAL


# ==========================================
# MAIN GAME LOOP
# ==========================================

while time.time() - start_time < GAME_TIME:

    # --------------------------------------
    # Click cookie many times
    # --------------------------------------

    for _ in range(20):

        try:
            driver.execute_script(
                "arguments[0].click();",
                cookie
            )
        except Exception:
            # Find cookie again if page changes
            cookie = driver.find_element(
                By.ID,
                "bigCookie"
            )

    # --------------------------------------
    # Every few seconds buy best product
    # --------------------------------------

    if time.time() >= next_check:

        try:
            products = driver.find_elements(
                By.CSS_SELECTOR,
                "#products .product.unlocked.enabled"
            )

            if products:
                # The most expensive available
                # unlocked product is at the bottom
                products[-1].click()

        except Exception as e:
            print("Product error:", e)

        next_check = time.time() + CHECK_INTERVAL


# ==========================================
# FINAL RESULT
# ==========================================

try:
    cookies = driver.find_element(
        By.ID,
        "cookies"
    ).text

    print("\n==============================")
    print("GAME FINISHED!")
    print("==============================")
    print("Final cookies:", cookies)

except Exception as e:
    print("Could not read final cookies:", e)