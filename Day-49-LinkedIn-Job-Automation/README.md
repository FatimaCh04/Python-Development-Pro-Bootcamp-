# 💼 Day 49 - LinkedIn Job Automation

## 100 Days of Python - Angela Yu

This is my Day 49 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

A Selenium-based LinkedIn job search automation
project.

The program opens LinkedIn Jobs, searches for
a specified job title and location, and collects
visible job listing information for manual review.

## ✨ Features

- Opens LinkedIn Jobs automatically
- Searches for a selected job title
- Searches by location
- Finds visible job cards
- Extracts job titles
- Extracts company names
- Extracts job locations
- Displays job information
- Uses Selenium WebDriver

## 📚 Topics Covered

- Selenium WebDriver
- Browser Automation
- Explicit Waits
- CSS Selectors
- `find_element()`
- `find_elements()`
- `.text`
- `.strip()`
- Exception Handling
- URL Parameters
- Web Automation

## 🛠 Technologies

- Python
- Selenium
- Google Chrome

## 📁 Project Structure

```text
Day-49-LinkedIn-Job-Automation/
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

Change the job title:

```python
JOB_TITLE = "Python Developer"
```

Change the location:

```python
LOCATION = "Pakistan"
```

## ▶️ Run

```bash
python main.py
```

The browser will open LinkedIn Jobs with
the selected search criteria.

## 📖 Learning Outcomes

Through Day 49 I learned how to:

- Automate browser tasks using Selenium
- Search websites programmatically
- Locate multiple web elements
- Extract information from job listings
- Work with CSS selectors
- Use explicit waits
- Handle dynamic webpages
- Build browser automation scripts

## ⚠️ Note

Websites can change their HTML structure,
so Selenium selectors may need to be updated.

This project is intended for learning browser
automation. Job applications should be reviewed
manually before submission.

