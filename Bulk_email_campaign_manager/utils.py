"""
utils.py
────────
Reusable helper functions and classes shared across the project.

Public API
──────────
ContactValidationResult  – dataclass holding the full validation report
ContactLoader            – class that loads, validates, and cleans a contacts CSV
  .load()                  → ContactValidationResult
  .print_summary()         → prints a pre-send table to the console

Standalone helpers (preserved from v1):
  load_contacts()        – thin wrapper around ContactLoader for backward compat
  render_template()      – fills HTML template {{placeholders}} from a contact dict
  validate_email()       – lightweight regex email format check
  already_sent()         – reads email_log.csv to prevent duplicate sends
  campaign_summary()     – prints a post-send stats table to the console
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from logger import EMAIL_LOG_FILE, get_logger

# Force stdout to UTF-8 on Windows so box-drawing chars and emojis print cleanly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

# Columns that MUST be present in contacts.csv
REQUIRED_COLUMNS = {"name", "email"}

# Regex for a syntactically valid email address
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ── Validation result dataclass ────────────────────────────────────────────────

@dataclass
class ContactValidationResult:
    """
    Holds every category of contact produced during CSV validation.

    Attributes:
        valid        : Contacts that passed all checks (ready to email).
        invalid      : Rows with a bad / missing email (list of dicts with
                       an extra 'reason' key explaining the problem).
        duplicates   : Rows removed because their email appeared earlier.
        empty_rows   : Number of fully blank rows skipped.
        total_raw    : Total rows in the CSV before any filtering.
    """
    valid: list[dict] = field(default_factory=list)
    invalid: list[dict] = field(default_factory=list)
    duplicates: list[dict] = field(default_factory=list)
    empty_rows: int = 0
    total_raw: int = 0

    # ── Convenience properties ─────────────────────────────────────────────────

    @property
    def total_valid(self) -> int:
        return len(self.valid)

    @property
    def total_invalid(self) -> int:
        return len(self.invalid)

    @property
    def total_duplicates(self) -> int:
        return len(self.duplicates)


# ── ContactLoader class ────────────────────────────────────────────────────────

class ContactLoader:
    """
    Loads a contacts CSV file and validates every row without ever raising an
    exception — all problems are reported in the returned ContactValidationResult.

    Usage:
        loader = ContactLoader("contacts.csv")
        result = loader.load()          # never crashes
        loader.print_summary(result)    # display table before sending
        contacts = result.valid         # pass to the email campaign
    """

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    # ── Public entry point ─────────────────────────────────────────────────────

    def load(self) -> ContactValidationResult:
        """
        Reads the CSV and runs all validation steps.
        Never raises — errors are captured into the result object.

        Steps:
          1. Check file existence
          2. Check for required columns
          3. Skip empty rows
          4. Validate email addresses
          5. Remove duplicate emails (keep first occurrence)

        Returns:
            ContactValidationResult with every category populated.
        """
        result = ContactValidationResult()

        # ── Step 1: file existence ─────────────────────────────────────────────
        if not self.csv_path.exists():
            logger.error(f"Contacts file not found: '{self.csv_path}'")
            return result  # all lists empty — caller handles gracefully

        # ── Step 2: parse CSV ──────────────────────────────────────────────────
        try:
            df = pd.read_csv(self.csv_path)
        except pd.errors.EmptyDataError:
            logger.warning(f"'{self.csv_path.name}' is empty — no contacts to load.")
            return result
        except Exception as exc:
            logger.error(f"Failed to read '{self.csv_path.name}': {exc}")
            return result

        result.total_raw = len(df)

        # Normalise column names
        df.columns = [col.strip().lower() for col in df.columns]

        # ── Step 3: required column check ─────────────────────────────────────
        missing_cols = REQUIRED_COLUMNS - set(df.columns)
        if missing_cols:
            logger.error(
                f"'{self.csv_path.name}' is missing required column(s): "
                f"{', '.join(sorted(missing_cols))}. "
                f"Required: {', '.join(sorted(REQUIRED_COLUMNS))}."
            )
            return result

        # Strip whitespace from all string columns
        str_cols = df.select_dtypes(include="object").columns
        df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

        # ── Step 4: skip completely empty rows ─────────────────────────────────
        before = len(df)
        df = df.dropna(how="all")
        result.empty_rows = before - len(df)
        if result.empty_rows:
            logger.debug(f"Skipped {result.empty_rows} fully empty row(s).")

        # ── Step 5: validate each row ──────────────────────────────────────────
        seen_emails: set[str] = set()

        for _, row in df.iterrows():
            contact = row.to_dict()
            email_raw = str(contact.get("email", "")).strip()
            name_raw = str(contact.get("name", "")).strip()

            # Missing or NaN email
            if not email_raw or email_raw.lower() == "nan":
                contact["reason"] = "Missing email address"
                result.invalid.append(contact)
                logger.debug(f"  Invalid (missing email): name='{name_raw}'")
                continue

            # Bad email format
            if not validate_email(email_raw):
                contact["reason"] = f"Invalid email format: '{email_raw}'"
                result.invalid.append(contact)
                logger.debug(f"  Invalid (bad format): '{email_raw}'")
                continue

            # Duplicate email (case-insensitive)
            email_key = email_raw.lower()
            if email_key in seen_emails:
                contact["reason"] = f"Duplicate email: '{email_raw}'"
                result.duplicates.append(contact)
                logger.debug(f"  Duplicate: '{email_raw}'")
                continue

            seen_emails.add(email_key)
            result.valid.append(contact)

        logger.info(
            f"Contact loading complete — "
            f"valid={result.total_valid}, "
            f"invalid={result.total_invalid}, "
            f"duplicates={result.total_duplicates}, "
            f"empty rows={result.empty_rows}."
        )
        return result

    # ── Summary printer ────────────────────────────────────────────────────────

    @staticmethod
    def print_summary(result: ContactValidationResult) -> None:
        """
        Prints a formatted pre-send contact report to the console.

        Args:
            result: The ContactValidationResult returned by .load().
        """
        border = "=" * 56
        thin   = "-" * 56

        print(f"\n{border}")
        print("  [CONTACTS]  Contact Validation Summary")
        print(border)
        print(f"  {'Total rows in CSV':<30}: {result.total_raw}")
        print(f"  {'Empty rows skipped':<30}: {result.empty_rows}")
        print(thin)
        print(f"  {'[OK]  Valid contacts':<30}: {result.total_valid}")
        print(f"  {'[ERR] Invalid contacts':<30}: {result.total_invalid}")
        print(f"  {'[DUP] Duplicate emails removed':<30}: {result.total_duplicates}")
        print(border)

        if result.total_invalid:
            print("\n  Invalid contact details:")
            for c in result.invalid:
                name  = c.get("name", "(no name)")
                email = c.get("email", "(no email)")
                reason = c.get("reason", "Unknown")
                print(f"    [X]  {name:<20} | {str(email):<28} | {reason}")

        if result.total_duplicates:
            print("\n  Duplicate emails removed (first occurrence kept):")
            for c in result.duplicates:
                name  = c.get("name", "(no name)")
                email = c.get("email", "(no email)")
                print(f"    [~]  {name:<20} | {email}")

        if result.total_valid == 0:
            print("\n  [STOP]  No valid contacts found -- nothing to send.")
        else:
            print(f"\n  [GO]    {result.total_valid} contact(s) ready to receive email.")

        print(f"{border}\n")


# ── Backward-compatible load_contacts() ───────────────────────────────────────

def load_contacts(csv_path: str | Path) -> list[dict]:
    """
    Thin wrapper around ContactLoader for backward compatibility.
    Returns only the valid contacts list.

    Used by email_sender.send_campaign() which expects a plain list[dict].

    Args:
        csv_path: Path to the contacts CSV file.

    Returns:
        List of validated contact dicts (valid only).
    """
    loader = ContactLoader(csv_path)
    result = loader.load()
    return result.valid


# ── Template rendering ─────────────────────────────────────────────────────────

def render_template(template_path: str | Path, contact: dict) -> str:
    """
    Reads an HTML template file and replaces {{placeholder}} tokens with
    values from the contact dict.

    Supported tokens map directly to CSV column names:
      {name}, {email}, {company}, {plan}, or any custom column. (Also supports {{name}} format)

    Args:
        template_path: Path to the HTML template file.
        contact: Dict of contact data (column → value).

    Returns:
        Rendered HTML string.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    html = load_email_template(template_path)

    for key, value in contact.items():
        # Skip internal keys added during validation (e.g. 'reason')
        if key == "reason":
            continue
        val_str = str(value) if pd.notna(value) else ""
        # Support both new {key} format and legacy {{key}} format
        html = html.replace("{" + str(key) + "}", val_str)
        html = html.replace("{{" + str(key) + "}}", val_str)

    return html

def load_email_template(template_path: str | Path) -> str:
    """
    Reads the HTML template file and returns its content as a string.

    Args:
        template_path: Path to the HTML template file.

    Returns:
        The raw HTML template string.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Email template not found: {template_path}")
    
    return template_path.read_text(encoding="utf-8")


# ── Email format validation ────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """
    Returns True if the email address looks syntactically valid.
    This is a lightweight regex check, not a live deliverability probe.
    """
    return bool(_EMAIL_RE.match(email.strip()))


# ── Duplicate-send guard ───────────────────────────────────────────────────────

def already_sent(email: str, subject: str) -> bool:
    """
    Returns True if email_log.csv contains a successful 'sent' entry
    for this (email, subject) combination.  Prevents re-sending on retries.
    """
    if not EMAIL_LOG_FILE.exists():
        return False

    try:
        df = pd.read_csv(EMAIL_LOG_FILE)
        mask = (
            (df["email"].str.strip().str.lower() == email.strip().lower())
            & (df["subject"].str.strip() == subject.strip())
            & (df["status"].str.strip() == "Sent")
        )
        return bool(mask.any())
    except Exception as exc:
        logger.warning(f"Could not read email log for duplicate check: {exc}")
        return False


# ── Post-send campaign summary ─────────────────────────────────────────────────

def campaign_summary(results: list[dict]) -> None:
    """
    Prints a formatted summary of the campaign run to the console.

    Args:
        results: List of dicts with keys: email, name, status, error.
    """
    total   = len(results)
    sent    = sum(1 for r in results if r["status"] == "Sent")
    failed  = sum(1 for r in results if r["status"] == "Failed")
    skipped = sum(1 for r in results if r["status"] == "Skipped")

    border = "─" * 50
    print(f"\n{border}")
    print("  📊  Campaign Summary")
    print(border)
    print(f"  Total contacts   : {total}")
    print(f"  ✅ Sent          : {sent}")
    print(f"  ❌ Failed        : {failed}")
    print(f"  ⏭  Skipped       : {skipped}")
    print(border)

    if failed:
        print("\n  Failed recipients:")
        for r in results:
            if r["status"] == "failed":
                print(f"    • {r['email']}  —  {r.get('error', 'Unknown error')}")
        print()
