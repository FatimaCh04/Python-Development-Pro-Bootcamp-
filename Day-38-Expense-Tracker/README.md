# 💰 Day 38 - Expense Tracker

## 📚 Course

100 Days of Python - Day 38 Practice

## 🎯 Topics Covered

- Google Sheets API
- API Authentication
- Service Accounts
- Environment Variables
- JSON Credentials
- Reading and Writing Spreadsheet Data
- Exception Handling
- Date and Time

## ✨ Features

- Add expenses
- Store expenses in Google Sheets
- View saved expenses
- Automatically record the date
- Categorize expenses
- Add notes
- Handle connection and input errors

## 🛠 Technologies

- Python 3
- Google Sheets API
- gspread
- OAuth2
- python-dotenv

## 📦 Installation

Install the required packages:

```bash
pip install gspread oauth2client python-dotenv
```

## ⚙️ Setup

Create a `.env` file:

```env
GOOGLE_SHEET_NAME=My Expenses
GOOGLE_CREDENTIALS_FILE=credentials.json
```

Add your Google service-account credentials as:

```text
credentials.json
```

Do NOT upload the credentials file to GitHub.

## ▶️ Run

```bash
python main.py
```

## 📊 Google Sheet Columns

The application creates:

| Date | Category | Amount | Note |
|------|----------|--------|------|

## 📖 Learning Outcomes

After completing this project, I practiced:

- Connecting Python applications to Google Sheets
- Using APIs
- Working with authentication
- Reading and writing spreadsheet data
- Managing credentials securely
- Handling exceptions
- Automating data entry