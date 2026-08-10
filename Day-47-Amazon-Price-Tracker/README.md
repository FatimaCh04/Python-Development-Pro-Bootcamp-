# 🛒 Day 47 - Automated Amazon Price Tracker

## 100 Days of Python - Angela Yu

This is my Day 47 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

An automated Amazon Price Tracker that checks
the price of a product and sends an email alert
when the price falls below a target price.

## ✨ How It Works

1. The program requests the Amazon product page.
2. BeautifulSoup parses the HTML.
3. The product title is extracted.
4. The current price is extracted.
5. The price is compared with the target price.
6. If the price is low enough, an email alert is sent.

## 📚 Topics Covered

- Web Scraping
- BeautifulSoup
- Requests
- `strip()`
- String manipulation
- Float conversion
- SMTP
- Email automation
- HTTP headers
- Conditional statements

## 🛠 Technologies

- Python
- Requests
- BeautifulSoup
- smtplib

## 📁 Project Structure

```text
Day-47-Amazon-Price-Tracker/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 📦 Installation

Install the required package:

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

Set the following values in `main.py`:

```python
URL = "YOUR_AMAZON_PRODUCT_URL"

TARGET_PRICE = 100.00

EMAIL = "YOUR_EMAIL@gmail.com"

PASSWORD = "YOUR_APP_PASSWORD"

RECIPIENT_EMAIL = "RECIPIENT_EMAIL@gmail.com"
```

## ▶️ Run

```bash
python main.py
```

## 📧 Email Alert

If the product price is less than or equal
to the target price, the program sends an
email containing:

- Product name
- Current price
- Target price
- Product URL

## 🔐 Security

Never upload email passwords, app passwords,
API keys or other secrets to GitHub.

Use environment variables or a `.env` file
for sensitive credentials.

## 📖 Learning Outcomes

Through Day 47 I learned how to:

- Scrape product information
- Parse HTML with BeautifulSoup
- Extract prices from webpages
- Clean scraped strings
- Convert strings to numbers
- Send emails using SMTP
- Automate price monitoring

