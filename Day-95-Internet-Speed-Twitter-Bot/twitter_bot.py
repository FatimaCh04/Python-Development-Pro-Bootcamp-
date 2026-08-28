import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException
)


class TwitterBot:

    def __init__(
        self,
        username,
        password
    ):
        self.username = username
        self.password = password

        options = webdriver.ChromeOptions()

        options.add_argument(
            "--start-maximized"
        )

        options.add_argument(
            "--disable-notifications"
        )

        self.driver = webdriver.Chrome(
            options=options
        )

        self.wait = WebDriverWait(
            self.driver,
            15
        )

    def login(self):

        print("\nOpening X...")

        self.driver.get(
            "https://x.com/i/flow/login"
        )

        try:
            username_input = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.NAME,
                        "text"
                    )
                )
            )

            username_input.send_keys(
                self.username
            )

            username_input.send_keys(
                Keys.ENTER
            )

            time.sleep(2)

            password_input = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.NAME,
                        "password"
                    )
                )
            )

            password_input.send_keys(
                self.password
            )

            password_input.send_keys(
                Keys.ENTER
            )

            time.sleep(5)

            print("✅ Login process completed.")

            return True

        except TimeoutException:

            print(
                "\n❌ Login fields could not "
                "be located."
            )

            print(
                "X may have changed its login "
                "page or requested verification."
            )

            return False

    def post_complaint(
        self,
        complaint
    ):

        try:

            if not self.login():
                return

            print(
                "\nOpening post composer..."
            )

            self.driver.get(
                "https://x.com/compose/post"
            )

            tweet_box = self.wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        '[data-testid="tweetTextarea_0"]'
                    )
                )
            )

            tweet_box.click()

            tweet_box.send_keys(
                complaint
            )

            time.sleep(1)

            post_button = self.wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        '[data-testid="tweetButton"]'
                    )
                )
            )

            post_button.click()

            time.sleep(3)

            print(
                "\n✅ Complaint posted successfully!"
            )

        except TimeoutException:

            print(
                "\n❌ Could not complete the "
                "Twitter/X automation."
            )

            print(
                "The website layout or login "
                "flow may have changed."
            )

        except WebDriverException as error:

            print(
                f"\n❌ Browser error: {error}"
            )

        finally:

            print(
                "\nClosing browser..."
            )

            self.driver.quit()