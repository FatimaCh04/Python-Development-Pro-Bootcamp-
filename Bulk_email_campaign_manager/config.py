"""
config.py
─────────
Loads and validates all configuration from environment variables (.env).

Usage:
    from config import settings
    print(settings.gmail_user)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (same folder as this file)
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    """
    Immutable settings object populated from environment variables.
    Raises EnvironmentError on start-up if required credentials are missing.
    """

    email_address: str = field(default_factory=lambda: os.environ.get("EMAIL_ADDRESS", ""))
    email_password: str = field(default_factory=lambda: os.environ.get("EMAIL_PASSWORD", ""))
    sender_name: str = field(default_factory=lambda: os.environ.get("SENDER_NAME", "Campaign Manager"))
    default_subject: str = field(
        default_factory=lambda: os.environ.get("DEFAULT_SUBJECT", "Important Update")
    )
    emails_per_batch: int = field(
        default_factory=lambda: int(os.environ.get("EMAILS_PER_BATCH", "50"))
    )
    batch_delay_seconds: int = field(
        default_factory=lambda: int(os.environ.get("BATCH_DELAY_SECONDS", "60"))
    )
    max_emails_per_hour: int = field(
        default_factory=lambda: int(os.environ.get("MAX_EMAILS_PER_HOUR", "50"))
    )

    # Gmail SMTP constants
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    def validate(self) -> None:
        """
        Raises EnvironmentError if required credentials are absent.
        Call this once at application startup.
        """
        missing = []
        if not self.email_address:
            missing.append("EMAIL_ADDRESS")
        if not self.email_password:
            missing.append("EMAIL_PASSWORD")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variable(s): {', '.join(missing)}.\n"
                "Please configure your .env file with your Gmail credentials."
            )

# Singleton – import this object everywhere
settings = Settings()

# ── Global Configuration Constants ─────────────────────────────────────────────
SMTP_SERVER = settings.smtp_host
SMTP_PORT = settings.smtp_port
MAX_EMAILS_PER_HOUR = settings.max_emails_per_hour
CONTACTS_FILE = "contacts.csv"
TEMPLATE_FILE = "email_template.html"
LOG_FILE = "email_log.csv"
