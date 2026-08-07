import smtplib
import random

# ================= EMAIL SETTINGS ================= #

MY_EMAIL = "fatimachoudhry94@gmail.com"
PASSWORD = "hsfh usut zwrs jqmu"

TO_EMAIL = "fatimachoudhry91@gmail.com"

# ================= READ QUOTES ================= #

with open("quotes.txt", "r", encoding="utf-8") as file:
    quotes = file.readlines()

quote = random.choice(quotes).strip()

# ================= EMAIL MESSAGE ================= #

message = f"""Subject:Daily Motivation 💪

Good Morning! ☀️

Today's Motivation:

"{quote}"

Keep learning.
Keep growing.
Never give up!

Have a wonderful day! 😊
"""

# ================= SEND EMAIL ================= #

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(MY_EMAIL, PASSWORD)

        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=TO_EMAIL,
            msg=message.encode("utf-8")
        )

    print("✅ Email Sent Successfully!")

except Exception as e:
    print("❌ Error:")
    print(e)