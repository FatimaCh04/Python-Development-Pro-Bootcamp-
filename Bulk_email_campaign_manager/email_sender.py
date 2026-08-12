"""
email_sender.py
───────────────
Handles all SMTP interaction and email construction.

Public API:
  EmailSender        – context-manager class; keeps one SMTP session open
      .send_email()  – builds and sends a single personalised HTML email
  send_campaign()    – orchestrates the full contact list, batching, and logging
"""

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import pandas as pd

from config import settings
from logger import get_logger, log_email_result
from utils import (
    already_sent,
    campaign_summary,
    load_contacts,
    render_template,
    validate_email,
)

logger = get_logger(__name__)


class EmailSender:
    """
    Wraps a single authenticated SMTP session with Gmail.

    Use as a context manager so the connection is always closed properly:

        with EmailSender() as sender:
            sender.send_email(...)
    """

    def __init__(self) -> None:
        self._smtp: Optional[smtplib.SMTP] = None

    # ── Context manager protocol ───────────────────────────────────────────────

    def __enter__(self) -> "EmailSender":
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._disconnect()
        # Returning False re-raises any exception that occurred inside the block
        return False

    # ── Connection management ──────────────────────────────────────────────────

    def _connect(self) -> None:
        """Opens a TLS-encrypted SMTP connection and logs in."""
        logger.info(f"Connecting to {settings.smtp_host}:{settings.smtp_port} …")
        try:
            self._smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
            self._smtp.ehlo()
            self._smtp.starttls()          # Upgrade to TLS
            self._smtp.ehlo()
            self._smtp.login(settings.email_address, settings.email_password)
            logger.info(f"Authenticated as {settings.email_address}.")
        except smtplib.SMTPAuthenticationError:
            raise PermissionError(
                "Gmail authentication failed. "
                "Make sure EMAIL_ADDRESS and EMAIL_PASSWORD are correct "
                "and that you are using a Gmail App Password (not your account password)."
            )
        except smtplib.SMTPException as exc:
            raise ConnectionError(f"SMTP connection error: {exc}") from exc

    def _disconnect(self) -> None:
        """Closes the SMTP connection gracefully."""
        if self._smtp:
            try:
                self._smtp.quit()
                logger.info("SMTP connection closed.")
            except smtplib.SMTPException:
                pass  # Already disconnected – ignore
            finally:
                self._smtp = None

    # ── Email construction & sending ───────────────────────────────────────────

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_body: str,
        plain_text_body: Optional[str] = None,
    ) -> None:
        """
        Constructs a MIME multipart email (plain-text fallback + HTML) and
        sends it through the open SMTP session.

        Args:
            to_email:         Recipient email address.
            to_name:          Recipient display name.
            subject:          Email subject line.
            html_body:        Rendered HTML content.
            plain_text_body:  Optional plain-text alternative (auto-generated if omitted).

        Raises:
            RuntimeError: If called without an active SMTP session.
            smtplib.SMTPException: On delivery failure.
        """
        if self._smtp is None:
            raise RuntimeError("EmailSender must be used as a context manager before calling send_email().")

        # Build multipart/alternative message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.sender_name} <{settings.email_address}>"
        msg["To"] = f"{to_name} <{to_email}>"

        # Plain-text fallback for clients that cannot render HTML
        if plain_text_body is None:
            plain_text_body = (
                f"Hello {to_name},\n\n"
                "Please view this email in an HTML-capable email client.\n\n"
                f"Subject: {subject}"
            )

        msg.attach(MIMEText(plain_text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        self._smtp.sendmail(settings.email_address, to_email, msg.as_string())


# ── Campaign orchestrator ──────────────────────────────────────────────────────

def send_campaign(
    contacts_csv: str | Path,
    template_html: str | Path,
    subject: Optional[str] = None,
    skip_duplicates: bool = True,
    progress_callback = None,
) -> list[dict]:
    """
    Loads contacts, renders the template for each, and sends emails in batches.

    Args:
        contacts_csv:    Path to the contacts CSV file.
        template_html:   Path to the HTML email template.
        subject:         Subject line (defaults to settings.default_subject).
        skip_duplicates: If True, skips contacts already logged as 'sent'.
        progress_callback: Optional callback(index, total, name, status) for GUI updates.

    Returns:
        List of result dicts: {email, name, status, error}
    """
    subject = subject or settings.default_subject
    contacts = load_contacts(contacts_csv)
    results: list[dict] = []

    logger.info(f"Starting campaign for {len(contacts)} contact(s). Subject: '{subject}'")
    total_contacts = len(contacts)

    window_start_time = time.time()
    emails_processed_in_window = 0

    with EmailSender() as sender:
        for index, contact in enumerate(contacts, start=1):
            email = str(contact.get("email", "")).strip()
            full_name = str(contact.get("name", "")).strip()
            if not full_name:
                first = str(contact.get("first_name", "")).strip()
                last  = str(contact.get("last_name",  "")).strip()
                full_name = f"{first} {last}".strip()
            full_name = full_name or email

            result = {"email": email, "name": full_name, "status": "unknown", "error": ""}

            # Personalize subject line
            subject_rendered = subject
            for key, value in contact.items():
                if key == "reason": continue
                val_str = str(value) if pd.notna(value) else ""
                subject_rendered = subject_rendered.replace("{" + str(key) + "}", val_str)
                subject_rendered = subject_rendered.replace("{{" + str(key) + "}}", val_str)

            # ── Pre-flight checks ──────────────────────────────────────────────
            if not validate_email(email):
                msg = f"Invalid email address: '{email}'"
                logger.warning(f"  ⚠  Skipping {full_name}: {msg}")
                result.update(status="Skipped", error=msg)
                results.append(result)
                log_email_result(email, full_name, subject_rendered, "Skipped", msg)
                if progress_callback:
                    progress_callback(index, total_contacts, full_name, "Skipped")
                continue

            if skip_duplicates and already_sent(email, subject_rendered):
                logger.info(f"  ⏭  Skipping {full_name} ({email}) – already sent.")
                result.update(status="Skipped", error="already sent")
                results.append(result)
                if progress_callback:
                    progress_callback(index, total_contacts, full_name, "Skipped")
                continue

            # ── Rate Limiting ──────────────────────────────────────────────────
            if emails_processed_in_window >= settings.max_emails_per_hour:
                elapsed = time.time() - window_start_time
                if elapsed < 3600:
                    print("Hourly limit reached. Waiting until the next sending window...")
                    time.sleep(3600 - elapsed)
                
                # Reset window
                window_start_time = time.time()
                emails_processed_in_window = 0

            # ── Render & send ──────────────────────────────────────────────────
            try:
                html_body = render_template(template_html, contact)
                sender.send_email(
                    to_email=email,
                    to_name=full_name,
                    subject=subject_rendered,
                    html_body=html_body,
                )
                result["status"] = "Sent"
                log_email_result(email, full_name, subject_rendered, "Sent")
                print(f"Sending {index}/{total_contacts} → {full_name} → Sent")
                if progress_callback:
                    progress_callback(index, total_contacts, full_name, "Sent")

            except smtplib.SMTPRecipientsRefused as exc:
                err = f"Recipient refused: {exc}"
                result.update(status="Failed", error=err)
                log_email_result(email, full_name, subject_rendered, "Failed", err)
                print(f"Sending {index}/{total_contacts} → {full_name} → Failed")
                if progress_callback:
                    progress_callback(index, total_contacts, full_name, "Failed")

            except smtplib.SMTPException as exc:
                err = f"SMTP error: {exc}"
                result.update(status="Failed", error=err)
                log_email_result(email, full_name, subject_rendered, "Failed", err)
                print(f"Sending {index}/{total_contacts} → {full_name} → Failed")
                if progress_callback:
                    progress_callback(index, total_contacts, full_name, "Failed")

            except Exception as exc:
                err = str(exc)
                result.update(status="Failed", error=err)
                log_email_result(email, full_name, subject_rendered, "Failed", err)
                print(f"Sending {index}/{total_contacts} → {full_name} → Failed")
                if progress_callback:
                    progress_callback(index, total_contacts, full_name, "Failed")

            results.append(result)
            emails_processed_in_window += 1

    campaign_summary(results)
    return results
