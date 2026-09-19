"""
Automated Mail Merge Engine
Stage 3 of the PDF Employee Data to Mail Merge Pipeline.

Reads every employee record from data/cleaned_employees.xlsx (or .csv),
renders each one against templates/employee_template.docx using docxtpl /
Jinja2, and writes one uniquely-named .docx file per employee into
output/word/.

Key behaviours
--------------
- Reads the real Excel file dynamically; no hard-coded row counts.
- Filename scheme: Employee_<Employee_ID>.docx
  Falls back to a safe sequential name if the ID is missing.
- Collision protection: appends _v2, _v3 … instead of overwriting.
- Special characters in names / IDs are stripped from filenames.
- All column values from the Excel sheet are passed as Jinja context,
  so the template can use ANY column without code changes.
- Failed records are logged to output/word/FAILED_RECORDS.txt instead of
  stopping the entire run.
- Prints "Processing employee N/TOTAL" for every record.
- Final summary: total / success / failed / output folder.
"""

import sys
import os
import re
import csv
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize_filename(text: str, max_len: int = 60) -> str:
    """
    Strips characters that are illegal in Windows/macOS/Linux filenames,
    collapses whitespace to underscores, and trims to *max_len* characters.
    Safe for any Unicode employee name.
    """
    # Remove forbidden chars: \ / * ? : " < > |  and control chars
    cleaned = re.sub(r'[\\/\*\?:"<>|\x00-\x1f\x7f]', "", str(text))
    # Collapse runs of whitespace / dashes / dots into a single underscore
    cleaned = re.sub(r"[\s\-\.]+", "_", cleaned)
    # Strip leading/trailing underscores or dots
    cleaned = cleaned.strip("._")
    # Enforce maximum length to avoid OS path limits
    return cleaned[:max_len] if cleaned else "unknown"


def unique_output_path(directory: Path, stem: str) -> Path:
    """
    Returns *directory/stem.docx*, incrementing a counter suffix (_v2, _v3 …)
    until an unused path is found.  Never overwrites an existing file.
    """
    candidate = directory / f"{stem}.docx"
    if not candidate.exists():
        return candidate
    counter = 2
    while True:
        candidate = directory / f"{stem}_v{counter}.docx"
        if not candidate.exists():
            return candidate
        counter += 1


def build_output_stem(row: Dict[str, Any], seq_index: int) -> str:
    """
    Constructs a clean filename stem from the employee record.
    Priority:  Employee_<employee_id>
    Fallback:  Employee_<seq_index:04d>
    """
    emp_id = str(row.get("employee_id") or "").strip()
    if emp_id and emp_id.lower() not in ("nan", "none", ""):
        return f"Employee_{sanitize_filename(emp_id)}"
    return f"Employee_{seq_index:04d}"


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------

def load_employee_records(data_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Loads employee records using pandas (preferred) or openpyxl / csv fallback.
    Returns (list_of_row_dicts, list_of_column_names).
    All cell values are normalised to str; NaN / None becomes "".
    """
    suffix = data_path.suffix.lower()

    # ---- pandas path -------------------------------------------------------
    try:
        import pandas as pd
        if suffix in (".xlsx", ".xls"):
            df = pd.read_excel(data_path, dtype=str, engine="openpyxl")
        else:
            df = pd.read_csv(data_path, dtype=str)
        df = df.fillna("")
        # Strip leading/trailing whitespace from all string cells
        df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)
        columns = list(df.columns)
        records = df.to_dict(orient="records")
        return records, columns

    except ImportError:
        pass  # fall through to openpyxl / csv

    # ---- openpyxl path (Excel) ---------------------------------------------
    if suffix in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(data_path), data_only=True, read_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            raw_header = next(rows_iter, None)
            if raw_header is None:
                return [], []
            columns = [
                str(c).strip() if c is not None else f"col_{i}"
                for i, c in enumerate(raw_header)
            ]
            records = []
            for raw_row in rows_iter:
                row_dict = {}
                for i, col in enumerate(columns):
                    val = raw_row[i] if i < len(raw_row) else None
                    row_dict[col] = str(val).strip() if val is not None else ""
                records.append(row_dict)
            wb.close()
            return records, columns
        except Exception as e:
            raise RuntimeError(f"Failed to read Excel file with openpyxl: {e}") from e

    # ---- csv path ----------------------------------------------------------
    records = []
    with open(data_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        for row in reader:
            records.append({k: (v.strip() if v else "") for k, v in row.items()})
    return records, columns


# ---------------------------------------------------------------------------
# Mail Merge Core
# ---------------------------------------------------------------------------

def build_context(row: Dict[str, Any], seq_index: int, total: int) -> Dict[str, Any]:
    """
    Builds the Jinja2 render context for a single employee record.
    Every column from the Excel sheet is included verbatim so the template
    can reference any field without code changes.  A small set of computed /
    guaranteed keys are also added.
    """
    ctx: Dict[str, Any] = {}

    # Pass through every column exactly as it appears in the data
    for key, val in row.items():
        ctx[key] = str(val) if val is not None else ""

    # Computed convenience keys (only set if not already in row)
    now = datetime.now()
    ctx.setdefault("current_date", now.strftime("%B %d, %Y"))
    ctx.setdefault("current_year", now.strftime("%Y"))
    ctx.setdefault("record_index", str(seq_index))
    ctx.setdefault("total_records", str(total))

    # Guaranteed employee_id / full_name so template never crashes on missing
    if not ctx.get("employee_id"):
        ctx["employee_id"] = f"EMP-{seq_index:04d}"

    full_name = ctx.get("full_name", "").strip()
    if not full_name:
        first = ctx.get("first_name", "")
        last = ctx.get("last_name", "")
        full_name = f"{first} {last}".strip() or "Unknown Employee"
        ctx["full_name"] = full_name

    # Derived first / last name if not present
    if not ctx.get("first_name"):
        parts = full_name.split()
        ctx["first_name"] = parts[0] if parts else ""
    if not ctx.get("last_name"):
        parts = full_name.split()
        ctx["last_name"] = parts[-1] if len(parts) > 1 else ""

    return ctx


def generate_mail_merge(
    data_path: Path,
    template_path: Path,
    output_dir: Path,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Main mail merge routine.

    Parameters
    ----------
    data_path    : Path to cleaned_employees.xlsx (or .csv)
    template_path: Path to employee_template.docx
    output_dir   : Folder for generated .docx files
    limit        : Optional max number of records to process

    Returns
    -------
    dict with keys: total, success, failed, output_dir, failed_records
    """
    from docxtpl import DocxTemplate

    # ---- Validate inputs ---------------------------------------------------
    if not data_path.exists():
        raise FileNotFoundError(
            f"Input data file not found: {data_path}\n"
            f"Run Stage 2 (clean_data.py) first to produce cleaned_employees.xlsx."
        )
    if not template_path.exists():
        raise FileNotFoundError(
            f"Word template not found: {template_path}\n"
            f"Run scripts/create_sample_template.py to generate it."
        )
    if data_path.stat().st_size == 0:
        raise ValueError(f"Input data file is empty (0 bytes): {data_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load data ---------------------------------------------------------
    print(f"[*] Loading employee records from: {data_path}")
    records, columns = load_employee_records(data_path)

    if not records:
        print("[!] No employee records found in the data file. Nothing to merge.")
        return {"total": 0, "success": 0, "failed": 0,
                "output_dir": str(output_dir), "failed_records": []}

    if limit and limit > 0:
        print(f"[*] --limit flag set: processing first {limit} of {len(records)} records.")
        records = records[:limit]

    total = len(records)
    print(f"[*] Total employee records to process : {total}")
    print(f"[*] Word template                     : {template_path}")
    print(f"[*] Output directory                  : {output_dir}")
    print(f"[*] Detected columns ({len(columns)})            : {', '.join(columns)}")
    print("-" * 68)

    count_success = 0
    count_failed = 0
    failed_records: List[Dict[str, Any]] = []

    for idx, row in enumerate(records, start=1):
        # Progress line – always printed
        print(f"  Processing employee {idx}/{total}", end="\r", flush=True)

        try:
            context = build_context(row, idx, total)
            stem = build_output_stem(row, idx)
            output_file = unique_output_path(output_dir, stem)

            # Re-instantiate template for every record to avoid rendering
            # state bleed between documents
            doc = DocxTemplate(str(template_path))
            doc.render(context)
            doc.save(str(output_file))

            count_success += 1
            # Print final confirmation on same line (overwrites progress)
            print(f"  [{idx:>{len(str(total))}}/{total}] OK  -> {output_file.name}")

        except Exception as exc:
            count_failed += 1
            error_detail = {
                "index": idx,
                "employee_id": str(row.get("employee_id", f"row-{idx}")),
                "full_name": str(row.get("full_name", "")),
                "error": str(exc),
            }
            failed_records.append(error_detail)
            print(f"  [{idx:>{len(str(total))}}/{total}] FAIL -> "
                  f"ID={error_detail['employee_id']} | {exc}")

    # ---- Write error report ------------------------------------------------
    if failed_records:
        report_path = output_dir / "FAILED_RECORDS.txt"
        with open(report_path, "w", encoding="utf-8") as rpt:
            rpt.write(f"Mail Merge Error Report\n")
            rpt.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            rpt.write("=" * 60 + "\n\n")
            for rec in failed_records:
                rpt.write(f"Index      : {rec['index']}\n")
                rpt.write(f"Employee ID: {rec['employee_id']}\n")
                rpt.write(f"Name       : {rec['full_name']}\n")
                rpt.write(f"Error      : {rec['error']}\n")
                rpt.write("-" * 40 + "\n")
        print(f"\n[!] Error report written to: {report_path}")

    # ---- Final summary -----------------------------------------------------
    print("\n" + "=" * 68)
    print("  MAIL MERGE COMPLETE")
    print("=" * 68)
    print(f"  Total records in file  : {total}")
    print(f"  Documents generated    : {count_success}")
    print(f"  Failed records         : {count_failed}")
    print(f"  Output folder          : {output_dir.resolve()}")
    if count_failed:
        print(f"  Error report           : {(output_dir / 'FAILED_RECORDS.txt').resolve()}")
    print("=" * 68 + "\n")

    return {
        "total": total,
        "success": count_success,
        "failed": count_failed,
        "output_dir": str(output_dir.resolve()),
        "failed_records": failed_records,
    }


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Stage 3 – Automated Mail Merge: generate one .docx per employee "
            "from cleaned_employees.xlsx using the Word template."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _base = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--data", "-d",
        type=Path,
        default=_base / "data" / "cleaned_employees.xlsx",
        help="Path to cleaned employee Excel (or CSV) file",
    )
    parser.add_argument(
        "--template", "-t",
        type=Path,
        default=_base / "templates" / "employee_template.docx",
        help="Path to the Word (.docx) template file",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=_base / "output" / "word",
        help="Output directory for generated Word documents",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Process only the first N records (useful for test runs)",
    )
    args = parser.parse_args()

    print("\n" + "=" * 68)
    print("  STAGE 3: AUTOMATED MAIL MERGE")
    print("=" * 68 + "\n")

    try:
        generate_mail_merge(
            data_path=args.data,
            template_path=args.template,
            output_dir=args.output_dir,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"\n[ERROR] Mail merge failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
