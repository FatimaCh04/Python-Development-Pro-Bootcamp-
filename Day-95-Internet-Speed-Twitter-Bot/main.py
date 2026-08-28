from internet_speed import InternetSpeedTester
from twitter_bot import TwitterBot
import os
from dotenv import load_dotenv


load_dotenv()


PROMISED_DOWNLOAD = float(
    os.getenv("PROMISED_DOWNLOAD", "50")
)

PROMISED_UPLOAD = float(
    os.getenv("PROMISED_UPLOAD", "10")
)


def main():
    print("=" * 60)
    print("        INTERNET SPEED TWITTER COMPLAINT BOT")
    print("=" * 60)

    print(
        f"\nPromised Download Speed: "
        f"{PROMISED_DOWNLOAD} Mbps"
    )

    print(
        f"Promised Upload Speed: "
        f"{PROMISED_UPLOAD} Mbps"
    )

    print("\nTesting your internet speed...\n")

    tester = InternetSpeedTester()

    download_speed, upload_speed = (
        tester.get_speed()
    )

    print(
        f"\nActual Download Speed: "
        f"{download_speed:.2f} Mbps"
    )

    print(
        f"Actual Upload Speed: "
        f"{upload_speed:.2f} Mbps"
    )

    download_problem = (
        download_speed < PROMISED_DOWNLOAD
    )

    upload_problem = (
        upload_speed < PROMISED_UPLOAD
    )

    if not download_problem and not upload_problem:
        print(
            "\n✅ Your internet speed meets "
            "the promised speed."
        )

        return

    print(
        "\n⚠️ Your internet speed is below "
        "the promised speed."
    )

    complaint = (
        "My internet provider promised me "
        f"{PROMISED_DOWNLOAD} Mbps download and "
        f"{PROMISED_UPLOAD} Mbps upload, but my "
        f"current speed is only "
        f"{download_speed:.2f} Mbps download and "
        f"{upload_speed:.2f} Mbps upload. "
        "Please investigate this issue."
    )

    print("\nComplaint:")
    print(complaint)

    twitter_username = os.getenv(
        "TWITTER_USERNAME"
    )

    twitter_password = os.getenv(
        "TWITTER_PASSWORD"
    )

    if not twitter_username or not twitter_password:
        print(
            "\n⚠️ Twitter/X credentials are not "
            "configured."
        )

        print(
            "\nThe complaint was generated "
            "successfully, but it was not posted."
        )

        print(
            "\nAdd your credentials to the "
            ".env file if you want to use "
            "browser automation."
        )

        return

    bot = TwitterBot(
        username=twitter_username,
        password=twitter_password
    )

    bot.post_complaint(complaint)


if __name__ == "__main__":
    main()