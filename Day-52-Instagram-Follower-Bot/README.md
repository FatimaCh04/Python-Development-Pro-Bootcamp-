# 📸 Day 52 - Instagram Follower Bot

## 100 Days of Python - Angela Yu

This is my Day 52 project from Angela Yu's
100 Days of Code: The Complete Python Pro Bootcamp.

## 🎯 Project

A Selenium-based Instagram automation project
based on the Instagram Follower Bot project.

The project demonstrates how Selenium can:

- Open Instagram
- Handle manual login
- Navigate to a profile
- Find page elements
- Inspect buttons
- Read element text
- Read HTML attributes
- Automate browser interaction

## ✨ Features

- Opens Instagram automatically
- Allows manual login
- Opens a target profile
- Inspects visible buttons
- Reads button text
- Reads ARIA attributes
- Displays page information
- Uses Selenium WebDriver

## 📚 Topics Covered

- Selenium WebDriver
- Browser Automation
- `find_element()`
- `find_elements()`
- `By.TAG_NAME`
- `By.XPATH`
- CSS Selectors
- `.text`
- `.get_attribute()`
- Explicit Waits
- Dynamic Webpages
- Exception Handling

## 🛠 Technologies

- Python
- Selenium
- Google Chrome

## 📁 Project Structure

```text
Day-52-Instagram-Follower-Bot/
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

Change the target profile:

```python
TARGET_PROFILE = "instagram"
```

For example:

```python
TARGET_PROFILE = "example_profile"
```

## ▶️ Run

```bash
python main.py
```

The browser will open Instagram.

If required, complete login and verification
manually.

The program will then open the target profile
and inspect available page elements.

## 🧠 Learning Outcomes

Through Day 52 I learned how to:

- Automate browsers with Selenium
- Navigate dynamic websites
- Locate web elements
- Read element text
- Read HTML attributes
- Use explicit waits
- Handle browser automation errors
- Work with dynamically loaded content

## ⚠️ Note

Instagram frequently changes its website structure,
selectors, login flow, and automation restrictions.

The original course project involved automating
Instagram following. This implementation focuses
on the Selenium learning concepts and avoids
blind mass-following on real accounts.
