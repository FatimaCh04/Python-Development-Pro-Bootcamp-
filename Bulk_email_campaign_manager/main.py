"""
main.py
───────
Entry point for the Automated Bulk Email Campaign Manager.

Usage examples:
    # Inspect contacts only (no emails sent):
    python main.py --contacts-info

    # Send now (one-shot):
    python main.py

    # Send with a custom subject:
    python main.py --subject "Q3 Newsletter"

    # Schedule daily at 09:00:
    python main.py --schedule daily --at 09:00

    # Schedule every 4 hours:
    python main.py --schedule hourly --every 4

    # Dry-run (validate contacts & template, no emails sent):
    python main.py --dry-run
"""

import argparse
import sys
from pathlib import Path

from config import settings, CONTACTS_FILE, TEMPLATE_FILE
from logger import get_logger
from scheduler import run_daily, run_every_hours, run_once, run_scheduler
from utils import ContactLoader, load_contacts, render_template

logger = get_logger(__name__)

BASE_DIR = Path(__file__).parent
DEFAULT_CONTACTS = BASE_DIR / CONTACTS_FILE
DEFAULT_TEMPLATE = BASE_DIR / TEMPLATE_FILE


# ── CLI argument parser ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-campaign-manager",
        description="Automated Bulk Email Campaign Manager – sends personalised HTML emails via Gmail SMTP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --cli
  python main.py --contacts-info
  python main.py --subject "Black Friday Sale!"
  python main.py --schedule daily --at 09:30
  python main.py --schedule hourly --every 6
  python main.py --dry-run
        """,
    )

    parser.add_argument(
        "--contacts",
        type=Path,
        default=DEFAULT_CONTACTS,
        help=f"Path to contacts CSV (default: {DEFAULT_CONTACTS.name})",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help=f"Path to HTML email template (default: {DEFAULT_TEMPLATE.name})",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="Override the email subject line.",
    )
    parser.add_argument(
        "--schedule",
        choices=["daily", "hourly"],
        default=None,
        help="Run on a recurring schedule: 'daily' or 'hourly'.",
    )
    parser.add_argument(
        "--at",
        type=str,
        default="08:00",
        metavar="HH:MM",
        help="Time for daily schedule in 24-hour format (default: 08:00).",
    )
    parser.add_argument(
        "--every",
        type=int,
        default=6,
        metavar="N",
        help="Interval in hours for hourly schedule (default: 6).",
    )
    parser.add_argument(
        "--no-skip-duplicates",
        action="store_true",
        help="Disable duplicate-send guard (re-send to all contacts).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate contacts & template only – no emails are sent.",
    )
    parser.add_argument(
        "--contacts-info",
        action="store_true",
        help="Show a contact validation summary and exit (no emails sent).",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force the interactive command-line interface instead of the GUI.",
    )

    return parser


# ── Contact validation helper ──────────────────────────────────────────────────

def validate_and_report_contacts(contacts_path: Path) -> list[dict]:
    """
    Runs the full ContactLoader pipeline, prints the summary table, and
    returns the list of valid contacts.

    Exits with code 1 if there are no valid contacts at all.

    Args:
        contacts_path: Path to the contacts CSV file.

    Returns:
        List of valid contact dicts ready for sending.
    """
    loader = ContactLoader(contacts_path)
    result = loader.load()
    ContactLoader.print_summary(result)

    if result.total_valid == 0:
        logger.error("No valid contacts found. Aborting.")
        sys.exit(1)

    return result.valid


# ── Dry-run mode ───────────────────────────────────────────────────────────────

def dry_run(contacts_path: Path, template_path: Path) -> None:
    """
    Full validation run:
      1. Loads and validates contacts (with printed summary table).
      2. Renders the template for the first valid contact.
      3. Exits without sending any emails.
    """
    logger.info("── DRY RUN MODE ──────────────────────────────────────")

    # Run full contact validation + print the summary table
    valid_contacts = validate_and_report_contacts(contacts_path)

    # Render a preview using the first valid contact
    if valid_contacts:
        try:
            rendered = render_template(template_path, valid_contacts[0])
            preview_len = 200
            logger.info(
                f"  Template preview : "
                f"{rendered[:preview_len]}{'…' if len(rendered) > preview_len else ''}"
            )
        except FileNotFoundError as exc:
            logger.error(str(exc))

    logger.info("  No emails were sent.")
    logger.info("── END DRY RUN ────────────────────────────────────────")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    # ── Launch GUI by default if no arguments (or only --gui) are passed ──────
    if len(sys.argv) == 1:
        try:
            from gui.main_window import MainWindow
            app = MainWindow()
            app.mainloop()
            return
        except ImportError as e:
            logger.error(f"Failed to load GUI: {e}. Falling back to CLI.")
            # Fall through to CLI if GUI fails to load

    parser = build_parser()
    args = parser.parse_args()

    # ── Contacts-info mode (no credential check needed) ───────────────────────
    if args.contacts_info:
        loader = ContactLoader(args.contacts)
        result = loader.load()
        ContactLoader.print_summary(result)
        return

    # ── All other modes require valid Gmail credentials ───────────────────────
    try:
        settings.validate()
    except EnvironmentError as exc:
        logger.error(str(exc))
        sys.exit(1)

    skip_duplicates = not args.no_skip_duplicates

    # ── Dry-run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        dry_run(args.contacts, args.template)
        return

    # ── Pre-flight: always show contact summary before sending ────────────────
    logger.info("Running contact validation before campaign start …")
    validate_and_report_contacts(args.contacts)
    # (exits with code 1 automatically if zero valid contacts)

    # ── Scheduled mode ────────────────────────────────────────────────────────
    if args.schedule == "daily":
        run_daily(
            at_time=args.at,
            contacts_csv=args.contacts,
            template_html=args.template,
            subject=args.subject,
            skip_duplicates=skip_duplicates,
        )
        run_scheduler()

    elif args.schedule == "hourly":
        run_every_hours(
            hours=args.every,
            contacts_csv=args.contacts,
            template_html=args.template,
            subject=args.subject,
            skip_duplicates=skip_duplicates,
        )
        run_scheduler()

    # ── Immediate one-shot (default) ──────────────────────────────────────────
    else:
        if not args.subject:
            args.subject = input("\nEnter email subject (e.g. Special Offer for {name}): ").strip()
            
        print("\nA. Send now")
        print("B. Schedule campaign")
        choice = input("Select an option (A/B): ").strip().upper()

        if choice == 'B':
            import re
            time_str = input("\nEnter campaign time (HH:MM): ").strip()
            if not re.match(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", time_str):
                print("Invalid time format. Please use HH:MM.")
                sys.exit(1)
            
            print(f"\nCampaign scheduled for {time_str}.")
            run_daily(
                at_time=time_str,
                contacts_csv=args.contacts,
                template_html=args.template,
                subject=args.subject,
                skip_duplicates=skip_duplicates,
            )
            run_scheduler()

        elif choice == 'A':
            # Ask for confirmation before starting
            confirm = input("\nStart campaign? (y/n): ").strip().lower()
            if confirm != 'y':
                logger.info("Campaign aborted by user.")
                sys.exit(0)
                
            run_once(
                contacts_csv=args.contacts,
                template_html=args.template,
                subject=args.subject,
                skip_duplicates=skip_duplicates,
            )
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)


if __name__ == "__main__":
    main()
