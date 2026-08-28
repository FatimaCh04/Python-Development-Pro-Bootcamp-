# 🚀 Day 95 — Internet Speed Twitter Complaint Bot

A Python automation project inspired by **Angela Yu's 100 Days of Code: The Complete Python Pro Bootcamp**.

The application measures the user's internet download and upload speeds, compares them with the promised speeds, and automatically prepares a complaint. When credentials are configured, Selenium can be used to open X and post the complaint.

---

## 🎯 Project Objective

Internet service providers often advertise a specific download and upload speed.

This project automates the process of:

1. Testing the current internet speed.
2. Comparing the actual speed with the promised speed.
3. Detecting whether the service is underperforming.
4. Generating a personalized complaint.
5. Using Selenium browser automation to post the complaint on X.

---

## ✨ Features

* 🌐 Internet speed testing
* 📥 Download speed measurement
* 📤 Upload speed measurement
* 📊 Promised vs actual speed comparison
* ⚠️ Automatic detection of poor performance
* 📝 Automatic complaint generation
* 🤖 Selenium browser automation
* 🔐 Environment-variable credential management
* 🛡️ `.env` excluded from Git
* ❌ Error handling for browser failures
* 🧩 Modular project structure

---

## 🛠️ Technologies

| Technology       | Purpose                    |
| ---------------- | -------------------------- |
| Python           | Main programming language  |
| Speedtest CLI    | Internet speed measurement |
| Selenium         | Browser automation         |
| Chrome WebDriver | Browser control            |
| python-dotenv    | Environment variables      |

---

## 📂 Project Structure

```text
Day-95-Internet-Speed-Twitter-Bot/
│
├── main.py
├── internet_speed.py
├── twitter_bot.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### 1. Create Virtual Environment

Windows:

```powershell
python -m venv venv
```

### 2. Activate Virtual Environment

PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## 🔐 Environment Configuration

Create a `.env` file in the project root.

Example:

```text
PROMISED_DOWNLOAD=50
PROMISED_UPLOAD=10

TWITTER_USERNAME=your_username
TWITTER_PASSWORD=your_password
```

Never commit your real `.env` file to GitHub.

---

## ▶️ Running the Project

Run:

```powershell
python main.py
```

The application will first test the internet connection.

Example:

```text
============================================================
        INTERNET SPEED TWITTER COMPLAINT BOT
============================================================

Promised Download Speed: 50 Mbps
Promised Upload Speed: 10 Mbps

Testing your internet speed...

Finding the best speed test server...
Testing download speed...
Testing upload speed...

Actual Download Speed: 32.45 Mbps
Actual Upload Speed: 7.82 Mbps

⚠️ Your internet speed is below the promised speed.
```

The application then generates a personalized complaint.

---

## 🤖 Selenium Automation

When Twitter/X credentials are configured, Selenium:

```text
Open X
   ↓
Open Login Page
   ↓
Enter Username
   ↓
Enter Password
   ↓
Open Post Composer
   ↓
Enter Complaint
   ↓
Submit Post
```

Modern websites can change their HTML structure and authentication process. If X changes its login or posting interface, the Selenium selectors may need to be updated.

---

## 🧠 Key Concepts Learned

This project demonstrates:

* Web automation
* Selenium WebDriver
* Browser interaction
* Explicit waits
* HTML element selection
* Keyboard automation
* Environment variables
* `.env` configuration
* Internet speed testing
* Object-oriented programming
* Conditional logic
* Exception handling
* Modular Python development

---

## 🔒 Security

Credentials should never be hard-coded directly into Python files.

Instead, the project uses environment variables:

```python
username = os.getenv("TWITTER_USERNAME")
password = os.getenv("TWITTER_PASSWORD")
```

The `.gitignore` file prevents `.env` from being committed.

---

## ⚠️ Important Notes

The original course project was created for an older version of Twitter.

X's website, authentication flow, and automation restrictions can change over time.

Therefore, Selenium automation may require selector updates or manual verification.

The internet-speed measurement and complaint-generation portions work independently from the X automation.

---

## 🚀 Future Improvements

Possible improvements include:

* Add graphical interface
* Save speed-test history
* Generate reports
* Add email notifications
* Add logging
* Support multiple internet providers
* Store results in SQLite
* Add scheduled speed testing
* Improve browser automation
* Add configurable complaint templates

---

## 📚 100 Days of Python

**Day 95 / 100 ✅**

This project strengthened my understanding of **Selenium, browser automation, internet speed testing, environment variables, object-oriented programming, and automated workflows**.

---

## 👩‍💻 Author

**Fatima Ch**

**100 Days of Python — Day 95/100**

> Learn • Build • Practice • Improve 🚀

---

## 📌 Project Status

**Completed ✅**
