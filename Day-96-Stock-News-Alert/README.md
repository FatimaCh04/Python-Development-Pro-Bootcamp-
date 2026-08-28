# 📈 Day 96 — Stock Trading News Alert

A Python automation project inspired by **Angela Yu's 100 Days of Code: The Complete Python Pro Bootcamp**.

This application monitors a stock's daily price movement and automatically checks for relevant news when a significant change is detected. It can also send the generated alert through SMS using Twilio.

## 🎯 Project Objective

The goal of this project is to combine **stock market data, news APIs, and automated notifications** into a practical Python application.

The program:

* Retrieves daily stock market data
* Compares the latest and previous closing prices
* Calculates the percentage change
* Detects significant price movements
* Fetches the latest company-related news
* Generates a concise alert
* Sends the alert through SMS when Twilio is configured

## ✨ Features

* 📊 Real-time stock data retrieval
* 📈 Percentage change calculation
* 🚨 Automatic price-movement detection
* 📰 Latest relevant news retrieval
* 📱 SMS notification support
* 🔐 Secure API-key configuration using `.env`
* 🧩 Modular Python architecture
* ⚠️ API and exception handling

## 🛠️ Technologies Used

* **Python**
* **Requests**
* **Alpha Vantage API**
* **NewsAPI**
* **Twilio**
* **python-dotenv**

## 📂 Project Structure

```text
Day-96-Stock-News-Alert/
│
├── main.py
├── stock_checker.py
├── news_checker.py
├── sms_sender.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 🔑 Environment Variables

Create a `.env` file based on `.env.example`:

```text
STOCK_SYMBOL=TSLA
COMPANY_NAME=Tesla

STOCK_API_KEY=your_alpha_vantage_api_key
NEWS_API_KEY=your_news_api_key

CHANGE_THRESHOLD=5

TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM=your_twilio_phone_number
TWILIO_TO=your_phone_number
```

Never upload your actual `.env` file or API credentials to GitHub.

## ▶️ Run the Application

```bash
python main.py
```

Example output:

```text
============================================================
        STOCK TRADING NEWS ALERT
============================================================

📈 Stock: TSLA
🏢 Company: Tesla

Testing stock data...

Today's change: -6.24%

🚨 Significant stock movement detected!

Headline: Tesla announces new updates
Brief: Latest company news and market developments...
```

If Twilio is configured, the alert is also sent by SMS.

## 🧠 Concepts Practiced

This project strengthened my understanding of:

* REST APIs
* HTTP requests
* JSON data processing
* API authentication
* Environment variables
* Object-Oriented Programming
* Exception handling
* Data comparison
* Automated notifications
* Modular Python development

## 🚀 Future Improvements

* Add email notifications
* Support multiple stocks
* Create a graphical dashboard
* Store historical stock data
* Add scheduled automatic checks
* Add charts and analytics
* Support Telegram notifications

## 📚 100 Days of Python

**Day 96 / 100 ✅**

This project provided hands-on experience with **APIs, financial data, news services, automation, and notification systems** while building a practical Python application.

---

### 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 96/100**

> Learn • Build • Practice • Improve 🚀
