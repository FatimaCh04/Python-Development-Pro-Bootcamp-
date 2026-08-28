import os
from dotenv import load_dotenv

from stock_checker import StockChecker
from news_checker import NewsChecker
from sms_sender import SMSSender


load_dotenv()

STOCK_SYMBOL = os.getenv("STOCK_SYMBOL", "TSLA")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Tesla")

STOCK_API_KEY = os.getenv("STOCK_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")

CHANGE_THRESHOLD = float(
    os.getenv("CHANGE_THRESHOLD", "5")
)


def main():

    print("=" * 60)
    print("        STOCK TRADING NEWS ALERT")
    print("=" * 60)

    if not STOCK_API_KEY:
        print("\n❌ STOCK_API_KEY is missing.")
        return

    if not NEWS_API_KEY:
        print("\n❌ NEWS_API_KEY is missing.")
        return

    print(f"\n📈 Stock: {STOCK_SYMBOL}")
    print(f"🏢 Company: {COMPANY_NAME}")

    stock_checker = StockChecker(
        api_key=STOCK_API_KEY,
        symbol=STOCK_SYMBOL
    )

    try:
        price_change, percentage_change = (
            stock_checker.get_price_change()
        )
    except Exception as error:
        print(f"\n❌ Stock API error: {error}")
        return

    print(
        f"\nToday's change: "
        f"{percentage_change:.2f}%"
    )

    if abs(percentage_change) < CHANGE_THRESHOLD:

        print(
            f"\nℹ️ Price movement is below "
            f"{CHANGE_THRESHOLD}%."
        )

        print("No news alert is required.")
        return

    if percentage_change > 0:
        direction = "🔺"
    else:
        direction = "🔻"

    print(
        f"\n🚨 Significant stock movement "
        f"detected! {direction}"
    )

    news_checker = NewsChecker(
        api_key=NEWS_API_KEY,
        company_name=COMPANY_NAME
    )

    try:
        articles = news_checker.get_news()
    except Exception as error:
        print(f"\n❌ News API error: {error}")
        return

    if not articles:
        print("\n⚠️ No recent news found.")

        message = (
            f"{STOCK_SYMBOL}: "
            f"{direction} "
            f"{percentage_change:.2f}%\n\n"
            f"No relevant news articles found."
        )

    else:

        message_parts = [
            f"{STOCK_SYMBOL}: "
            f"{direction} "
            f"{percentage_change:.2f}%"
        ]

        for article in articles:
            message_parts.append(
                f"\nHeadline: {article['title']}"
            )

            message_parts.append(
                f"Brief: {article['description']}"
            )

        message = "\n".join(message_parts)

    print("\n" + "-" * 60)
    print(message)
    print("-" * 60)

    if all(
        [
            TWILIO_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_FROM,
            TWILIO_TO
        ]
    ):

        sender = SMSSender(
            account_sid=TWILIO_SID,
            auth_token=TWILIO_AUTH_TOKEN,
            from_number=TWILIO_FROM,
            to_number=TWILIO_TO
        )

        try:
            sender.send(message)
            print("\n✅ SMS alert sent successfully.")

        except Exception as error:
            print(f"\n❌ SMS error: {error}")

    else:

        print(
            "\nℹ️ Twilio credentials are not "
            "configured."
        )

        print(
            "Alert was generated successfully "
            "but no SMS was sent."
        )


if __name__ == "__main__":
    main()