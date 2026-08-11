# 🏠 Day 53 - Automated Data Entry Job

## 100 Days of Python - Angela Yu

This is my Day 53 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

An automated data-entry workflow that combines
web scraping and browser automation.

The program:

1. Retrieves webpage data using Requests.
2. Parses HTML using BeautifulSoup.
3. Extracts structured information.
4. Opens a web form using Selenium.
5. Enters the extracted information into form fields.

## ✨ Features

- Web scraping
- HTML parsing
- Data extraction
- Selenium browser automation
- Automatic form filling
- Multiple-record processing

## 📚 Topics Covered

- Requests
- BeautifulSoup
- Selenium
- Web Scraping
- CSS Selectors
- `find_elements()`
- `send_keys()`
- Loops
- Dictionaries
- Exception handling
- Browser automation

## 🛠 Technologies

- Python
- Requests
- BeautifulSoup
- Selenium
- Google Chrome

## 📁 Project Structure

```text
Day-53-Automated-Data-Entry/
│
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 📦 Installation

Install all required packages:

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

Replace:

```python
FORM_URL = "https://docs.google.com/forms/"
```

with your own Google Form URL.

The form should contain fields for:

- Address
- Price
- Link

## ▶️ Run

```bash
python main.py
```

## 🔄 Workflow

```text
Web Page
   ↓
Requests
   ↓
BeautifulSoup
   ↓
Extract Data
   ↓
Selenium
   ↓
Google Form
   ↓
Enter Data
```

## 📖 Learning Outcomes

Through Day 53 I learned how to:

- Scrape webpage information
- Parse HTML using BeautifulSoup
- Store scraped data in Python dictionaries
- Automate browser interaction with Selenium
- Locate input fields
- Enter information using `send_keys()`
- Process multiple records automatically
- Combine web scraping and browser automation

## ⚠️ Note

Website structures can change over time.

Selectors may need to be updated when using
different websites or forms.

The project is intended for educational purposes
and demonstrates automated data-entry concepts.
