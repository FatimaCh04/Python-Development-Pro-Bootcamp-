import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse


# ==========================================
# 1. GET AMAZON PRODUCT URL
# ==========================================

URL = input("Paste the Amazon product URL: ").strip()


# Agar user Markdown format paste kare:
# [https://amazon.com/...](https://amazon.com/...)
if URL.startswith("[") and "](" in URL:
    URL = URL.split("](")[1].split(")")[0]


# Agar URL ke start/end mein quotes hon
URL = URL.strip('"').strip("'")


# ==========================================
# 2. BASIC URL VALIDATION
# ==========================================

if not URL.startswith(("http://", "https://")):
    print("\n❌ Invalid URL.")
    print("URL should start with https://")
    print("\nExample:")
    print("https://www.amazon.com/dp/B00ZHJDT7U")
    exit()


# ==========================================
# 3. AMAZON HEADERS
# ==========================================

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


# ==========================================
# 4. REQUEST AMAZON PAGE
# ==========================================

print("\n🔎 Checking Amazon product page...")

try:

    response = requests.get(
        URL,
        headers=headers,
        timeout=20
    )

except requests.exceptions.RequestException as error:

    print("\n❌ Request failed.")
    print(error)
    exit()


print(f"HTTP Status Code: {response.status_code}")


# ==========================================
# 5. CHECK RESPONSE
# ==========================================

if response.status_code != 200:

    print("\n❌ Amazon did not return a normal page.")

    if response.status_code == 503:
        print("Amazon returned 503 - Service Unavailable.")

    elif response.status_code == 403:
        print("Amazon blocked the request with 403.")

    else:
        print(f"Amazon returned status code: {response.status_code}")

    exit()


# ==========================================
# 6. SAVE HTML FOR DEBUGGING
# ==========================================

with open(
    "amazon_page.html",
    "w",
    encoding="utf-8"
) as file:

    file.write(response.text)


# ==========================================
# 7. PARSE HTML
# ==========================================

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ==========================================
# 8. GET PRODUCT TITLE
# ==========================================

title = None


title_element = soup.find(
    id="productTitle"
)

if title_element:

    title = title_element.get_text(
        strip=True
    )


# Fallback title
if not title:

    title_element = soup.find(
        "span",
        class_="product-title-word-break"
    )

    if title_element:

        title = title_element.get_text(
            strip=True
        )


if not title:

    title = "Amazon Product"


print("\n📦 Product:")
print(title)


# ==========================================
# 9. FIND PRICE
# ==========================================

price = None


# Amazon ke common price selectors
price_selectors = [

    "#corePriceDisplay_desktop_feature_div "
    ".a-price .a-offscreen",

    "#corePrice_feature_div "
    ".a-price .a-offscreen",

    "#priceblock_ourprice",

    "#priceblock_dealprice",

    "#priceblock_saleprice",

    "#price_inside_buybox",

    "#newBuyBoxPrice",

    "#tp_price_block_total_price_ww",

    ".priceToPay .a-offscreen",

    ".apexPriceToPay .a-offscreen",

    ".a-price.aok-align-center "
    ".a-offscreen",

    ".a-price .a-offscreen",
]


# ==========================================
# 10. TRY PRICE SELECTORS
# ==========================================

for selector in price_selectors:

    element = soup.select_one(selector)

    if element:

        text = element.get_text(
            strip=True
        )

        if text:

            price = text
            break


# ==========================================
# 11. TRY DATA ATTRIBUTES
# ==========================================

if not price:

    price_element = soup.find(
        attrs={
            "data-a-color": "price"
        }
    )

    if price_element:

        price_text = price_element.get_text(
            strip=True
        )

        if price_text:

            price = price_text


# ==========================================
# 12. TRY JSON-LD PRODUCT DATA
# ==========================================

if not price:

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    for script in scripts:

        try:

            script_text = script.string

            if not script_text:
                continue

            # Search for price inside JSON
            match = re.search(
                r'"price"\s*:\s*"?(?:USD)?\s*([0-9]+(?:\.[0-9]{1,2})?)',
                script_text,
                re.IGNORECASE
            )

            if match:

                price = "$" + match.group(1)
                break

        except Exception:
            continue


# ==========================================
# 13. SEARCH COMMON PRICE PATTERNS
# ==========================================

if not price:

    page_text = soup.get_text(
        " ",
        strip=True
    )

    # Example:
    # $29.99
    # $1,299.99
    matches = re.findall(
        r'\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
        page_text
    )

    if matches:

        # First reasonable price
        for match in matches:

            cleaned = match.replace(
                ",",
                ""
            )

            number = re.search(
                r'\d+(?:\.\d+)?',
                cleaned
            )

            if number:

                value = float(
                    number.group()
                )

                # Avoid obviously incorrect tiny values
                if value > 0:

                    price = match
                    break


# ==========================================
# 14. PRICE RESULT
# ==========================================

if price:

    print("\n" + "=" * 50)

    print("✅ PRICE FOUND!")

    print("=" * 50)

    print(f"\n📦 Product:")
    print(title)

    print(f"\n💰 Current Price:")
    print(price)

    print("\n" + "=" * 50)

else:

    print("\n❌ Price could not be found.")

    print(
        "\nAmazon returned the page, "
        "but the product price was not available "
        "in the HTML received by Python."
    )

    print(
        "\nThis can happen because Amazon "
        "changes its page structure or "
        "returns different content to automated requests."
    )

    print(
        "\n📄 The complete Amazon HTML has been saved to:"
    )

    print(
        "amazon_page.html"
    )

    print(
        "\nOpen amazon_page.html in VS Code "
        "to inspect the returned page."
    )


# ==========================================
# 15. END
# ==========================================

print("\nDone.")