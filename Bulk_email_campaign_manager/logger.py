"""
logger.py
─────────
Centralised logging for the campaign manager.

Provides:
  - get_logger()   : returns a configured logging.Logger instance
  - log_email_result() : appends a row to email_log.csv for audit trail
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path

from config import LOG_FILE

# ── Directory that holds this file ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

LOG_FILE_PATH = BASE_DIR / "app.log"
EMAIL_LOG_FILE = BASE_DIR / LOG_FILE

# ── CSV columns for the email audit log ───────────────────────────────────────
EMAIL_LOG_HEADERS = ["timestamp", "name", "email", "subject", "status", "error"]


def get_logger(name: str = "email_campaign") -> logging.Logger:
    """
    Returns a logger that writes to both the console and app.log.
    Calling this multiple times with the same name returns the same logger.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured – avoid duplicate handlers
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler (DEBUG and above) – full detail for troubleshooting
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def _ensure_email_log_headers() -> None:
    """Creates email_log.csv with header row if it does not already exist."""
    if not EMAIL_LOG_FILE.exists():
        with open(EMAIL_LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EMAIL_LOG_HEADERS)
            writer.writeheader()


def log_email_result(
    email: str,
    name: str,
    subject: str,
    status: str,          # "Sent" | "Failed" | "Skipped"
    error: str = "",
) -> None:
    """
    Appends one result row to email_log.csv.
    Creates the file with headers on first call.
    Handles file-writing errors gracefully.
    """
    try:
        _ensure_email_log_headers()
    except IOError as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to create email_log.csv headers: {e}")
        return

    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "email": email,
        "subject": subject,
        "status": status,
        "error": error,
    }

    try:
        with open(EMAIL_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EMAIL_LOG_HEADERS)
            writer.writerow(row)
    except IOError as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to write to email_log.csv: {e}")
