# 🐍 Day 51 - Internet Speed Twitter Complaint Bot

## 100 Days of Python - Angela Yu

This is my Day 51 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

An Internet Speed Complaint Bot that uses
Selenium to automate an internet speed test,
compare the actual speed with the promised
internet plan, and prepare a complaint message.

## ✨ How It Works

1. Opens Speedtest.net.
2. Starts an internet speed test.
3. Reads the download speed.
4. Reads the upload speed.
5. Compares the results with the promised plan.
6. Determines whether the internet speed is too low.
7. Generates a complaint message.

## 📚 Topics Covered

- Selenium WebDriver
- Browser Automation
- CSS Selectors
- Finding Web Elements
- Clicking Elements
- Regular Expressions
- Data Extraction
- Conditional Statements
- String Formatting
- Automation Logic

## 🛠 Technologies

- Python
- Selenium
- Chrome
- Speedtest.net

## 📁 Project Structure

```text
Day-51-Internet-Speed-Twitter-Bot/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 📦 Installation

Install Selenium:

```bash
pip install selenium
```

## ⚙️ Configuration

Set your internet plan speed:

```python
PROMISED_DOWNLOAD = 50
PROMISED_UPLOAD = 10
```

For example:

```text
Download: 50 Mbps
Upload: 10 Mbps
```

## ▶️ Run

```bash
python main.py
```

The browser will open Speedtest and
perform the speed test.

## 📊 Example

```text
Promised Download: 50 Mbps
Actual Download: 32.45 Mbps

Promised Upload: 10 Mbps
Actual Upload: 7.21 Mbps
```

The program will then generate a complaint
message.

## 📖 Learning Outcomes

Through Day 51 I learned how to:

- Automate websites using Selenium
- Extract information from webpages
- Work with CSS selectors
- Use regular expressions
- Compare actual and expected values
- Generate automated messages
- Build an automation workflow

## ⚠️ Note

Website structures and automation requirements
can change over time.

The original course project uses Twitter
automation. Modern Twitter/X may require
different selectors and authentication flows.

This version focuses on the core educational
concepts while keeping the final social-media
posting step for manual review.
