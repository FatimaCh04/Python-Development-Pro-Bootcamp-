# 📧 Automated Bulk Email Campaign Manager

A professional, modular Python application that sends **personalised HTML emails** to a list of contacts loaded from a CSV file — powered by Gmail SMTP, Pandas, and the `schedule` library.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Personalised HTML emails** | `{{placeholder}}` tokens auto-filled from any CSV column |
| **Batch sending** | Configurable batch size + delay to respect Gmail rate limits |
| **Duplicate guard** | Skips contacts already logged as successfully sent |
| **Audit log** | Every send attempt (sent / failed / skipped) written to `email_log.csv` |
| **Dual logging** | Human-readable output to console **and** `app.log` |
| **Scheduled runs** | Daily at a fixed time *or* every N hours via CLI flags |
| **Dry-run mode** | Validates contacts & template without sending a single email |
| **No hardcoded secrets** | All credentials come from a `.env` file |

---

## 🗂️ Project Structure

```
automated-bulk-email-campaign-manager/
│
├── main.py              ← CLI entry point (argparse)
├── config.py            ← Settings loaded from .env (immutable dataclass)
├── email_sender.py      ← SMTP session manager + campaign orchestrator
├── scheduler.py         ← Daily / hourly / one-shot scheduling
├── logger.py            ← Console + file logger + CSV audit trail
├── utils.py             ← Contact loading, template rendering, helpers
│
├── contacts.csv         ← Sample contacts (email, first_name, last_name, …)
├── email_template.html  ← Personalised HTML email template
├── email_log.csv        ← Auto-generated audit log (git-ignored)
│
├── requirements.txt     ← Third-party dependencies only
├── .env.example         ← Copy → .env and add your credentials
├── .gitignore           ← Keeps .env and logs out of version control
└── README.md            ← This file
```

---

## 🚀 Quick Start

### 1 — Clone & enter the directory

```bash
git clone <your-repo-url>
cd automated-bulk-email-campaign-manager
```

### 2 — Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Configure credentials

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Now open `.env` and fill in your values:

```env
EMAIL_ADDRESS=you@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
SENDER_NAME=Your Company Name
```

> ⚠️ **Important:** You must use a **Gmail App Password**, not your account password.  
> Generate one at → [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)  
> You also need **2-Step Verification** enabled on the account.

### 5 — Add your contacts

Edit `contacts.csv` or replace it entirely. Required columns:

| Column | Required | Description |
|---|---|---|
| `email` | ✅ Yes | Recipient email address |
| `first_name` | ✅ Yes | Used in `{{first_name}}` placeholder |
| `last_name` | ✅ Yes | Used in `{{last_name}}` placeholder |
| `company` | ➕ Optional | Any extra column becomes a `{{placeholder}}` |
| `plan` | ➕ Optional | Same as above |

### 6 — Run

```bash
# Send now (one-shot)
python main.py

# Custom subject
python main.py --subject "Q3 Newsletter – Exclusive for You"

# Schedule: daily at 09:00
python main.py --schedule daily --at 09:00

# Schedule: every 4 hours
python main.py --schedule hourly --every 4

# Dry-run (validate only, no emails sent)
python main.py --dry-run
```

---

## 🔧 Configuration Reference

All options live in `.env`. See `.env.example` for the full template.

| Variable | Default | Description |
|---|---|---|
| `EMAIL_ADDRESS` | *(required)* | Your Gmail address |
| `EMAIL_PASSWORD` | *(required)* | 16-character Gmail App Password |
| `SENDER_NAME` | `Campaign Manager` | Display name in the inbox |
| `DEFAULT_SUBJECT` | `Important Update` | Subject used when `--subject` is not passed |
| `EMAILS_PER_BATCH` | `50` | Emails sent before a pause |
| `BATCH_DELAY_SECONDS` | `60` | Seconds to pause between batches |
| `MAX_EMAILS_PER_HOUR` | `50` | Maximum number of emails to send per hour |

---

## 📝 HTML Template Guide

The template at `email_template.html` supports `{placeholder}` (or `{{placeholder}}`) tokens that map **directly** to column names in `contacts.csv`.

```html
Hi {name},

Your plan at {company} is: {plan}
```

Add any column to `contacts.csv` and the corresponding `{column_name}` will be replaced automatically — no code changes needed.

---

## 📊 Audit Log (`email_log.csv`)

Every send attempt is recorded:

| Column | Description |
|---|---|
| `timestamp` | When the attempt was made |
| `recipient_email` | Target address |
| `recipient_name` | Full name |
| `subject` | Email subject |
| `status` | `sent` / `failed` / `skipped` |
| `error` | Error message if status is `failed` or `skipped` |

> The duplicate-send guard reads this file. If you want to re-send to everyone, either delete `email_log.csv` or pass `--no-skip-duplicates`.

---

## 🏗️ Architecture & Module Responsibilities

```
main.py          CLI parsing → delegates to scheduler or email_sender
config.py        Reads .env → Settings dataclass (single source of truth)
email_sender.py  EmailSender (SMTP session) + send_campaign() orchestrator
scheduler.py     Wraps send_campaign() in schedule jobs + blocking loop
logger.py        Python logger (console + file) + CSV audit trail writer
utils.py         load_contacts, render_template, validate_email, already_sent
```

---

## 🔒 Security Notes

- **Never commit `.env`** — it is listed in `.gitignore`.
- Use a **dedicated Gmail account** for sending campaigns, not your personal account.
- Gmail App Passwords are account-specific and can be revoked at any time from your Google Account settings.
- `email_log.csv` may contain PII (names and email addresses) — it is also git-ignored.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `pandas` | ≥ 2.0 | CSV loading and audit log reading |
| `python-dotenv` | ≥ 1.0 | Loading `.env` credentials |
| `schedule` | ≥ 1.2 | Recurring job scheduling |
| `smtplib` | stdlib | Gmail SMTP communication |
| `email.mime` | stdlib | MIME email construction |
| `logging` | stdlib | Dual console + file logging |
| `csv` | stdlib | Audit log writing |

---

## 🛣️ Extending the Project

The modular design makes it straightforward to add:

- **Attachments** → extend `EmailSender.send_email()` with `MIMEBase` parts
- **Multiple templates** → add a `--template` column to `contacts.csv`
- **Unsubscribe list** → add a `utils.is_unsubscribed()` check in `send_campaign()`
- **Database back-end** → swap `load_contacts()` in `utils.py` for a DB query
- **REST API** → wrap `send_campaign()` with FastAPI/Flask endpoints
- **HTML report** → post-process `email_log.csv` with pandas and export HTML

---

## 📄 License

MIT — free to use, modify, and distribute.
