"""
scheduler.py
────────────
Provides scheduled / recurring campaign execution using the `schedule` library.

Public API:
  run_once()         – fires the campaign immediately (blocking until done)
  run_daily()        – schedules the campaign at a fixed time every day
  run_every_hour()   – schedules the campaign to run every N hours
  run_scheduler()    – starts the blocking scheduler loop (call after setup)
  stop_scheduler()   – signals the loop to exit cleanly
"""

import threading
import time
from pathlib import Path
from typing import Optional

import schedule

from config import settings, CONTACTS_FILE, TEMPLATE_FILE
from email_sender import send_campaign
from logger import get_logger

logger = get_logger(__name__)

# Default paths (resolved relative to this file's directory)
_BASE_DIR = Path(__file__).parent
_DEFAULT_CONTACTS = _BASE_DIR / CONTACTS_FILE
_DEFAULT_TEMPLATE = _BASE_DIR / TEMPLATE_FILE

# Shared stop-flag so the scheduler loop can be halted from another thread
_stop_event = threading.Event()


# ── One-shot helper ────────────────────────────────────────────────────────────

def run_once(
    contacts_csv: Path = _DEFAULT_CONTACTS,
    template_html: Path = _DEFAULT_TEMPLATE,
    subject: Optional[str] = None,
    skip_duplicates: bool = True,
) -> list[dict]:
    """
    Runs the email campaign immediately and returns the results list.

    Args:
        contacts_csv:    Path to contacts CSV.
        template_html:   Path to HTML template.
        subject:         Override the default subject line.
        skip_duplicates: If True, skips already-sent addresses.
    """
    logger.info("▶  Running campaign now (one-shot).")
    return send_campaign(
        contacts_csv=contacts_csv,
        template_html=template_html,
        subject=subject,
        skip_duplicates=skip_duplicates,
    )


# ── Schedule builders ──────────────────────────────────────────────────────────

def run_daily(
    at_time: str = "08:00",
    contacts_csv: Path = _DEFAULT_CONTACTS,
    template_html: Path = _DEFAULT_TEMPLATE,
    subject: Optional[str] = None,
    skip_duplicates: bool = True,
) -> None:
    """
    Registers a daily job that fires at `at_time` (24-hour "HH:MM" format).

    Example:
        run_daily(at_time="09:30")
        run_scheduler()   # blocks until stop_scheduler() is called
    """
    def _job():
        logger.info(f"⏰ Scheduled daily job triggered at {at_time}.")
        send_campaign(
            contacts_csv=contacts_csv,
            template_html=template_html,
            subject=subject,
            skip_duplicates=skip_duplicates,
        )

    schedule.every().day.at(at_time).do(_job)
    logger.info(f"Daily campaign scheduled at {at_time} every day.")


def run_every_hours(
    hours: int = 6,
    contacts_csv: Path = _DEFAULT_CONTACTS,
    template_html: Path = _DEFAULT_TEMPLATE,
    subject: Optional[str] = None,
    skip_duplicates: bool = True,
) -> None:
    """
    Registers a recurring job that fires every `hours` hours.

    Example:
        run_every_hours(hours=4)
        run_scheduler()
    """
    def _job():
        logger.info(f"⏰ Scheduled job triggered (every {hours}h).")
        send_campaign(
            contacts_csv=contacts_csv,
            template_html=template_html,
            subject=subject,
            skip_duplicates=skip_duplicates,
        )

    schedule.every(hours).hours.do(_job)
    logger.info(f"Campaign scheduled to run every {hours} hour(s).")


# ── Scheduler loop ─────────────────────────────────────────────────────────────

def run_scheduler(poll_interval: int = 30) -> None:
    """
    Blocking loop that checks for pending scheduled jobs every `poll_interval`
    seconds.  Call stop_scheduler() from another thread to exit cleanly.

    Args:
        poll_interval: Seconds between schedule checks (default 30 s).
    """
    _stop_event.clear()
    logger.info("Scheduler started. Press Ctrl+C or call stop_scheduler() to exit.")
    try:
        while not _stop_event.is_set():
            schedule.run_pending()
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user (Ctrl+C).")
    finally:
        schedule.clear()
        logger.info("Scheduler stopped. All jobs cleared.")


def stop_scheduler() -> None:
    """
    Signals the run_scheduler() loop to exit on its next poll iteration.
    Safe to call from any thread.
    """
    _stop_event.set()
    logger.info("Stop signal sent to scheduler.")
