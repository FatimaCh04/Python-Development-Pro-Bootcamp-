"""
Sales Data Analyzer Pro — Main Entry Point
Professional CLI with validated date filtering, module orchestration,
comprehensive exception handling, logging, and execution time display.
"""
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime, date
from pathlib import Path

# ── Ensure project root is on sys.path ────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import LOG_FILE, LOGS_DIR, CLEANED_DATA_FILE

# ───────────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ───────────────────────────────────────────────────────────────────────────
LOGS_DIR.mkdir(parents=True, exist_ok=True)

import io

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            if hasattr(sys.stdout, "buffer") else sys.stdout
        ),
    ],
)
logger = logging.getLogger("SalesDataAnalyzerPro")

# ───────────────────────────────────────────────────────────────────────────
# DISPLAY HELPERS
# ───────────────────────────────────────────────────────────────────────────
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _print_banner() -> None:
    print(f"""
{BOLD}{CYAN}
  +-------------------------------------------------+
  |          SALES DATA ANALYZER PRO                |
  |          Production v2.0                        |
  +-------------------------------------------------+
{RESET}{DIM}         Powered by Python | Pandas | Scikit-Learn{RESET}
""")

def _print_menu() -> None:
    print(f"{BOLD}{CYAN}{'='*52}{RESET}")
    print(f"{BOLD}  MAIN MENU{RESET}")
    print(f"{CYAN}{'='*52}{RESET}")
    items = [
        ("1", "Clean Data"),
        ("2", "Sales Analysis"),
        ("3", "Generate Charts"),
        ("4", "Show Top Products"),
        ("5", "Predict Future Sales"),
        ("6", "Generate PDF Report"),
        ("7", "Launch Web Dashboard"),
        ("8", "Run Full Pipeline"),
        ("9", "Exit"),
    ]
    for num, label in items:
        print(f"  {CYAN}{num}.{RESET}  {label}")
    print(f"{CYAN}{'='*52}{RESET}")

def _ok(msg: str) -> None:
    print(f"  {GREEN}[OK]{RESET}  {msg}")

def _err(msg: str) -> None:
    print(f"  {RED}[ERR]{RESET} {msg}")

def _info(msg: str) -> None:
    print(f"  {YELLOW}[>>]{RESET} {msg}")

def _timing(seconds: float) -> None:
    print(f"\n{DIM}  Execution time: {seconds:.3f}s{RESET}\n")


# ───────────────────────────────────────────────────────────────────────────
# DATE VALIDATION
# ───────────────────────────────────────────────────────────────────────────
DATE_FMT = "%Y-%m-%d"

def _ask_date(prompt: str, allow_empty: bool = True) -> date | None:
    """
    Prompts the user for a date (YYYY-MM-DD format).

    Parameters
    ----------
    prompt      : Input prompt text.
    allow_empty : If True, pressing Enter skips the filter.

    Returns
    -------
    date | None
    """
    while True:
        raw = input(f"  {YELLOW}{prompt}{RESET}").strip()
        if not raw and allow_empty:
            return None
        try:
            parsed = datetime.strptime(raw, DATE_FMT).date()
            return parsed
        except ValueError:
            _err(f"Invalid date '{raw}'. Please use YYYY-MM-DD format (e.g. 2023-01-31).")

def _ask_date_range() -> tuple[date | None, date | None]:
    """
    Interactively asks for an optional start and end date.
    Validates that start <= end.

    Returns
    -------
    (start_date, end_date) — either may be None (no filter applied).
    """
    print(f"\n{DIM}  Enter date range to filter data (press Enter to skip):{RESET}")
    while True:
        start = _ask_date("  Start date (YYYY-MM-DD) : ")
        end   = _ask_date("  End date   (YYYY-MM-DD) : ")
        if start and end and start > end:
            _err("Start date must not be after end date. Please try again.")
            continue
        return start, end


# ───────────────────────────────────────────────────────────────────────────
# FILTERED DATA LOADER
# ───────────────────────────────────────────────────────────────────────────
def _load_filtered(start: date | None, end: date | None):
    """Loads the cleaned dataset, optionally filtered by date range."""
    import pandas as pd
    if not CLEANED_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {CLEANED_DATA_FILE}.\n"
            "  Run option 1 (Clean Data) first."
        )
    df = pd.read_csv(CLEANED_DATA_FILE)
    df["Date"] = pd.to_datetime(df["Date"])
    if start:
        df = df[df["Date"].dt.date >= start]
    if end:
        df = df[df["Date"].dt.date <= end]
    if df.empty:
        raise ValueError("No data found for the specified date range.")
    _info(f"Loaded {len(df):,} records"
          f"{f' from {start}' if start else ''}"
          f"{f' to {end}'     if end   else ''}.")
    return df


# ───────────────────────────────────────────────────────────────────────────
# MENU ACTIONS
# ───────────────────────────────────────────────────────────────────────────
def action_clean() -> None:
    """Runs the complete data cleaning pipeline."""
    from src.utils    import generate_sample_data
    from src.cleaning import DataCleaner

    logger.info("Action: Clean Data")
    t0 = time.perf_counter()

    _info("Checking for raw dataset…")
    generate_sample_data()

    cleaner = DataCleaner()
    cleaner.clean_data()
    cleaner.save_cleaned_data()

    _timing(time.perf_counter() - t0)
    logger.info("Data cleaning completed.")
    _ok("Cleaning complete. See data/cleaned_sales_data.csv")


def action_analyze(start: date | None, end: date | None) -> None:
    """Runs the data analysis module."""
    from src.analysis import DataAnalyzer
    import pandas as pd

    logger.info("Action: Sales Analysis")
    t0 = time.perf_counter()

    df = _load_filtered(start, end)

    # Temporarily write filtered CSV for the analyzer to consume
    _tmp = CLEANED_DATA_FILE.parent / "_tmp_filtered.csv"
    df.to_csv(_tmp, index=False)

    try:
        analyzer = DataAnalyzer(data_file=_tmp)
        stats    = analyzer.analyze()

        print(f"\n{BOLD}{'='*50}{RESET}")
        print(f"{BOLD}  SUMMARY STATISTICS{RESET}")
        print(f"{'='*50}")
        for k, v in stats.items():
            val_str = f"${float(v):,.2f}" if k in ("Total Sales","Total Profit","Average Order Value") else str(v)
            print(f"  {CYAN}{k:<28}{RESET} {val_str}")
        print(f"{'='*50}\n")
    finally:
        _tmp.unlink(missing_ok=True)

    _timing(time.perf_counter() - t0)
    logger.info("Sales analysis completed.")


def action_charts(start: date | None, end: date | None) -> None:
    """Generates all visualisation charts."""
    from src.visualization import Visualizer
    import pandas as pd

    logger.info("Action: Generate Charts")
    t0 = time.perf_counter()

    df  = _load_filtered(start, end)
    _tmp = CLEANED_DATA_FILE.parent / "_tmp_filtered.csv"
    df.to_csv(_tmp, index=False)

    try:
        vis = Visualizer(data_file=_tmp)
        vis.generate_all_charts()
        _ok("All charts saved to charts/ directory.")
    finally:
        _tmp.unlink(missing_ok=True)

    _timing(time.perf_counter() - t0)
    logger.info("Chart generation completed.")


def action_top_products(start: date | None, end: date | None) -> None:
    """Displays top/bottom product rankings."""
    from src.analysis import DataAnalyzer
    import pandas as pd

    logger.info("Action: Top Products")
    t0 = time.perf_counter()

    df   = _load_filtered(start, end)
    _tmp = CLEANED_DATA_FILE.parent / "_tmp_filtered.csv"
    df.to_csv(_tmp, index=False)

    try:
        analyzer = DataAnalyzer(data_file=_tmp)
        analyzer.load_data()
        analyzer.generate_categorical_sales()
        analyzer.generate_rankings()
        analyzer.display_rankings()
    finally:
        _tmp.unlink(missing_ok=True)

    _timing(time.perf_counter() - t0)
    logger.info("Top products report completed.")


def action_predict(start: date | None, end: date | None) -> None:
    """Trains/loads the ML model and displays predictions."""
    from src.prediction import SalesPredictor
    import pandas as pd

    logger.info("Action: Predict Future Sales")
    t0 = time.perf_counter()

    df   = _load_filtered(start, end)
    _tmp = CLEANED_DATA_FILE.parent / "_tmp_filtered.csv"
    df.to_csv(_tmp, index=False)

    try:
        predictor   = SalesPredictor(data_file=_tmp)
        metrics     = predictor.train_model()
        predictions = predictor.predict_future()
        predictor.display_metrics()

        print(f"\n{BOLD}  SALES FORECAST{RESET}")
        print(f"  Next Month  : {GREEN}${predictions['Next_Month_Sales']:>15,.2f}{RESET}")
        print(f"  Next Quarter: {GREEN}${predictions['Next_Quarter_Sales']:>15,.2f}{RESET}\n")
    finally:
        _tmp.unlink(missing_ok=True)

    _timing(time.perf_counter() - t0)
    logger.info("Prediction completed.")


def action_pdf(start: date | None, end: date | None) -> None:
    """Generates the professional PDF report."""
    from src.cleaning    import DataCleaner
    from src.prediction  import SalesPredictor
    from src.pdf_report  import PDFReportGenerator

    logger.info("Action: Generate PDF Report")
    t0 = time.perf_counter()

    # Cleaning summary
    cleaner  = DataCleaner()
    cleaner.load_data()
    cleaner.clean_data()
    c_summary = cleaner.summary

    # ML metrics
    df   = _load_filtered(start, end)
    _tmp = CLEANED_DATA_FILE.parent / "_tmp_filtered.csv"
    df.to_csv(_tmp, index=False)

    try:
        predictor   = SalesPredictor(data_file=_tmp)
        metrics     = predictor.train_model()
        metrics["train_size"] = len(predictor.X_train) if predictor.X_train is not None else "N/A"
        metrics["test_size"]  = len(predictor.X_test)  if predictor.X_test  is not None else "N/A"
        predictions = predictor.predict_future()

        dr_str = ""
        if start or end:
            dr_str = f"{start or 'Start'} to {end or 'End'}"

        report = PDFReportGenerator(date_range=dr_str or "Full Dataset")
        report.generate(metrics=metrics, predictions=predictions, cleaning_summary=c_summary)
        _ok(f"PDF saved to {report.output_path}")
    finally:
        _tmp.unlink(missing_ok=True)

    _timing(time.perf_counter() - t0)
    logger.info("PDF report generated.")


def action_dashboard() -> None:
    """Launches the Streamlit web dashboard in a subprocess."""
    logger.info("Action: Launch Dashboard")
    _info("Launching Streamlit dashboard in your browser…")
    _info("Press Ctrl+C in the terminal to stop the server.")
    print()
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "dashboard.py",
             "--server.headless", "false"],
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    except KeyboardInterrupt:
        _info("Dashboard server stopped.")
    logger.info("Dashboard session ended.")


def action_full_pipeline() -> None:
    """Runs the complete pipeline end-to-end."""
    logger.info("Action: Full Pipeline")
    t0 = time.perf_counter()

    _info("Step 1/5 — Cleaning data…")
    action_clean()

    _info("Step 2/5 — Running analysis…")
    action_analyze(None, None)

    _info("Step 3/5 — Generating charts…")
    action_charts(None, None)

    _info("Step 4/5 — Training ML model & predicting…")
    action_predict(None, None)

    _info("Step 5/5 — Generating PDF report…")
    action_pdf(None, None)

    _timing(time.perf_counter() - t0)
    _ok("Full pipeline completed successfully!")
    logger.info("Full pipeline run completed.")


# ───────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ───────────────────────────────────────────────────────────────────────────
def _main_loop() -> None:
    _print_banner()
    logger.info("Application started.")

    # Date range is asked once per session; user can re-enter from the menu
    start_date: date | None = None
    end_date:   date | None = None

    while True:
        _print_menu()

        if start_date or end_date:
            _info(f"Active date filter: {start_date or 'Open'} → {end_date or 'Open'}")

        try:
            choice = input(f"  {BOLD}Select option (1-9) : {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            _info("Interrupt received — exiting.")
            logger.info("Application exited via keyboard interrupt.")
            break

        # ── Date filter shortcut ── enter 'd' to update dates
        if choice.lower() == "d":
            start_date, end_date = _ask_date_range()
            continue

        if choice not in {str(i) for i in range(1, 10)}:
            _err(f"Invalid choice '{choice}'. Please enter a number between 1 and 9.")
            continue

        # Actions that support date filtering ask at first use
        DATE_AWARE_ACTIONS = {"2", "3", "4", "5", "6"}
        if choice in DATE_AWARE_ACTIONS and start_date is None and end_date is None:
            print(f"\n{DIM}  Tip: Filter data by date? (Enter to use full dataset){RESET}")
            start_date, end_date = _ask_date_range()

        try:
            if choice == "1":
                action_clean()

            elif choice == "2":
                action_analyze(start_date, end_date)

            elif choice == "3":
                action_charts(start_date, end_date)

            elif choice == "4":
                action_top_products(start_date, end_date)

            elif choice == "5":
                action_predict(start_date, end_date)

            elif choice == "6":
                action_pdf(start_date, end_date)

            elif choice == "7":
                action_dashboard()

            elif choice == "8":
                action_full_pipeline()

            elif choice == "9":
                _ok("Goodbye!")
                logger.info("Application exited normally.")
                break

        except FileNotFoundError as e:
            _err(str(e))
            logger.error(f"FileNotFoundError: {e}")

        except ValueError as e:
            _err(str(e))
            logger.error(f"ValueError: {e}")

        except PermissionError as e:
            _err(f"Permission denied: {e}")
            logger.error(f"PermissionError: {e}")

        except KeyboardInterrupt:
            print()
            _info("Action cancelled by user.")
            logger.warning("Action interrupted by user (Ctrl+C).")

        except Exception as e:
            _err(f"Unexpected error: {e}")
            logger.exception(f"Unhandled exception: {e}")

        print()   # breathing room between menu cycles


# ───────────────────────────────────────────────────────────────────────────
# ARGUMENT PARSER  (--run-all flag for automated mode)
# ───────────────────────────────────────────────────────────────────────────
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sales Data Analyzer Pro",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run the complete pipeline non-interactively and exit.",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Optional start date filter for --run-all mode.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Optional end date filter for --run-all mode.",
    )
    return parser.parse_args()


# ───────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ───────────────────────────────────────────────────────────────────────────
def main() -> None:
    args = _parse_args()

    if args.run_all:
        # ── Non-interactive automated mode ──
        _print_banner()
        start = None
        end   = None

        if args.start_date:
            try:
                start = datetime.strptime(args.start_date, DATE_FMT).date()
            except ValueError:
                _err(f"Invalid --start-date '{args.start_date}'. Use YYYY-MM-DD.")
                sys.exit(1)

        if args.end_date:
            try:
                end = datetime.strptime(args.end_date, DATE_FMT).date()
            except ValueError:
                _err(f"Invalid --end-date '{args.end_date}'. Use YYYY-MM-DD.")
                sys.exit(1)

        if start and end and start > end:
            _err("--start-date must not be after --end-date.")
            sys.exit(1)

        logger.info("Running in automated mode (--run-all)")
        t_total = time.perf_counter()
        try:
            action_clean()
            action_analyze(start, end)
            action_charts(start, end)
            action_predict(start, end)
            action_pdf(start, end)
        except Exception as e:
            _err(f"Pipeline failed: {e}")
            logger.exception(f"Automated pipeline failed: {e}")
            sys.exit(1)

        _timing(time.perf_counter() - t_total)
        _ok("Automated run completed successfully.")
        logger.info("Automated run completed.")
    else:
        _main_loop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}  Interrupted. Goodbye!{RESET}")
        logger.info("Application exited via keyboard interrupt at top level.")
        sys.exit(0)
