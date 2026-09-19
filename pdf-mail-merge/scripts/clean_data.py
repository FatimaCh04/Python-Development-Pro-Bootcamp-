"""
Data Cleaning and Validation Engine
Cleans, normalizes, validates, and standardizes extracted employee records from data/employees.xlsx.

Key Requirements:
1. Loads extracted Excel data (data/employees.xlsx) using pandas.
2. Normalizes column names to canonical schema.
3. Removes completely empty rows.
4. Removes duplicate rows and detects duplicate employee records.
5. Cleans whitespace from all text fields.
6. Handles blank/null values safely without crashing.
7. Validates that required employee fields exist (employee_id, full_name).
8. STRICT INTEGRITY: Does NOT invent or fabricate missing employee information.
9. Generates an audit validation report (total, valid, invalid, missing fields, duplicates).
10. Saves outputs to data/cleaned_employees.xlsx and data/cleaned_employees.csv.
11. Prints clear terminal summary.
"""

import sys
import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Canonical alias mapping for standard employee attributes
COLUMN_ALIASES: Dict[str, List[str]] = {
    "employee_id": [
        "id", "emp_id", "employee id", "employee_id", "staff id", "empid",
        "badge", "id_number", "emp id", "employee no", "emp no", "serial no"
    ],
    "full_name": [
        "name", "full name", "employee name", "staff name", "emp_name",
        "worker name", "employee", "personnel name"
    ],
    "first_name": ["first name", "firstname", "fname", "first"],
    "last_name": ["last name", "lastname", "lname", "last", "surname"],
    "email": [
        "email", "email address", "e-mail", "mail", "corporate email", "work email"
    ],
    "phone": [
        "phone", "phone number", "contact", "telephone", "mobile", "cell", "tel"
    ],
    "department": [
        "department", "dept", "division", "unit", "team", "business unit"
    ],
    "job_title": [
        "job title", "title", "position", "role", "designation", "job role", "occupation"
    ],
    "hire_date": [
        "hire date", "start date", "date of joining", "doj", "joining date",
        "hire_date", "commencement date", "joined on", "service date"
    ],
    "salary": [
        "salary", "annual salary", "base salary", "compensation", "pay", "wage",
        "remuneration", "gross salary", "annual compensation"
    ],
    "employment_status": [
        "status", "employment status", "employment type", "state", "contract type"
    ],
    "manager": [
        "manager", "supervisor", "reporting manager", "reports to", "lead", "team lead"
    ],
    "location": [
        "location", "office", "city", "site", "branch", "workplace", "region"
    ],
    "performance_tier": [
        "performance", "rating", "performance tier", "grade", "evaluation", "score"
    ]
}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DEFAULT_REQUIRED_FIELDS = ["employee_id", "full_name"]


def match_canonical_column(col_name: str) -> str:
    """Matches a raw column header to its canonical equivalent using alias dictionary."""
    clean_col = re.sub(r"[^a-zA-Z0-9\s_]", "", str(col_name).strip().lower())
    clean_col = re.sub(r"\s+", " ", clean_col)

    for canonical, aliases in COLUMN_ALIASES.items():
        if clean_col == canonical:
            return canonical
        if clean_col in aliases:
            return canonical
        for alias in aliases:
            if alias in clean_col:
                return canonical

    return clean_col.replace(" ", "_")


def format_currency_safely(val: Any) -> Tuple[str, Optional[float]]:
    """
    Standardizes currency representation ($XX,XXX.XX) without inventing missing data.
    If value is null or empty, returns empty string and None.
    """
    if val is None:
        return "", None

    raw = str(val).strip()
    if raw == "" or raw.lower() in ("nan", "none", "null", "<na>", "n/a"):
        return "", None

    cleaned_num = re.sub(r"[^\d.]", "", raw)
    try:
        num = float(cleaned_num)
        return f"${num:,.2f}", num
    except (ValueError, TypeError):
        return raw, None


def standardize_date_safely(val: Any) -> str:
    """
    Parses diverse date formats into standardized YYYY-MM-DD.
    If date is missing or null, returns empty string without inventing a date.
    """
    if val is None:
        return ""

    raw = str(val).strip()
    if raw == "" or raw.lower() in ("nan", "none", "null", "<na>", "n/a"):
        return ""

    from datetime import datetime
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return raw


def load_input_data(input_path: Path):
    """
    Loads extracted employee data from Excel (.xlsx/.xls) or CSV using pandas,
    with fallback to openpyxl/csv if pandas is not available.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found at: '{input_path}'.\n"
            f"Please run the PDF extraction stage first to produce 'data/employees.xlsx'."
        )

    # Check for empty file
    if input_path.stat().st_size == 0:
        raise ValueError(f"Input file '{input_path}' is an empty 0-byte file.")

    try:
        import pandas as pd
        if input_path.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(input_path, dtype=str, engine="openpyxl")
        else:
            df = pd.read_csv(input_path, dtype=str)
        return df

    except ImportError:
        # Graceful fallback using openpyxl directly
        print("[*] pandas not imported in environment; using openpyxl fallback...")
        import openpyxl
        wb = openpyxl.load_workbook(str(input_path), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows or len(rows) <= 1:
            raise ValueError(f"No records found in '{input_path}'.")

        header = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(rows[0])]
        data = []
        for r in rows[1:]:
            row_dict = {header[i]: str(r[i]).strip() if i < len(r) and r[i] is not None else "" for i in range(len(header))}
            data.append(row_dict)

        # Build a minimal DataFrame-like container
        class MinimalDataFrame:
            def __init__(self, data_dicts, columns):
                self.columns = columns
                self._data = data_dicts
            def __len__(self):
                return len(self._data)
            def to_dict(self, orient="records"):
                return self._data

        return MinimalDataFrame(data, header)


def clean_and_validate_dataframe(
    df,
    required_fields: Optional[List[str]] = None
) -> Tuple[Any, Any, Dict[str, Any]]:
    """
    Performs comprehensive data cleaning and validation:
    1. Normalizes column names
    2. Strips completely blank rows
    3. Cleans whitespace from all text cells
    4. Handles null/blank values safely without crashing
    5. Deduplicates identical rows and detects duplicate employee IDs/records
    6. Validates required fields (employee_id, full_name) without inventing data
    7. Generates complete validation report
    """
    if required_fields is None:
        required_fields = list(DEFAULT_REQUIRED_FIELDS)

    try:
        import pandas as pd
        is_pandas = isinstance(df, pd.DataFrame)
    except ImportError:
        is_pandas = False

    # Extract list of dicts for universal, safe row-level manipulation
    if is_pandas:
        initial_count = len(df)
        raw_columns = [str(c) for c in df.columns]
        raw_records = df.to_dict(orient="records")
    else:
        initial_count = len(df)
        raw_columns = df.columns
        raw_records = df.to_dict(orient="records")

    report: Dict[str, Any] = {
        "total_records": initial_count,
        "empty_rows_removed": 0,
        "exact_duplicates_removed": 0,
        "duplicate_records": 0,
        "duplicate_employee_ids": [],
        "invalid_records": 0,
        "valid_records": 0,
        "missing_fields": {},
        "columns_normalized": {},
        "invalid_email_count": 0
    }

    if initial_count == 0:
        return df, df, report

    # 1. Normalize Column Names
    rename_map = {col: match_canonical_column(col) for col in raw_columns}
    report["columns_normalized"] = rename_map

    # 2. Process Records: Clean Whitespace, Remove Empty Rows, Handle Nulls Safely
    cleaned_records: List[Dict[str, Any]] = []
    seen_row_hashes = set()

    for row in raw_records:
        # Remap column names to canonical schema and clean cell whitespace
        clean_row: Dict[str, str] = {}
        for orig_k, val in row.items():
            canonical_k = rename_map.get(orig_k, orig_k)
            if val is None:
                cleaned_val = ""
            else:
                str_val = str(val).strip()
                # Remove "nan", "None", "null", "<NA>" artifacts
                if str_val.lower() in ("nan", "none", "null", "<na>"):
                    cleaned_val = ""
                else:
                    # Collapse multiple internal whitespace
                    cleaned_val = re.sub(r"\s+", " ", str_val)
            clean_row[canonical_k] = cleaned_val

        # Check for completely empty row
        if not any(v != "" for v in clean_row.values()):
            report["empty_rows_removed"] += 1
            continue

        # Check for exact duplicate row
        row_tuple = tuple(sorted(clean_row.items()))
        if row_tuple in seen_row_hashes:
            report["exact_duplicates_removed"] += 1
            continue
        seen_row_hashes.add(row_tuple)

        # Synthesize full_name if first_name / last_name exist but full_name is blank
        if not clean_row.get("full_name"):
            first = clean_row.get("first_name", "")
            last = clean_row.get("last_name", "")
            if first or last:
                clean_row["full_name"] = f"{first} {last}".strip()

        # Format existing values without inventing missing data
        if clean_row.get("full_name"):
            clean_row["full_name"] = clean_row["full_name"].title()

        if clean_row.get("employee_id"):
            clean_row["employee_id"] = clean_row["employee_id"].replace(".0", "").strip()

        if "salary" in clean_row and clean_row["salary"]:
            formatted_sal, num_sal = format_currency_safely(clean_row["salary"])
            clean_row["salary"] = formatted_sal
            clean_row["salary_numeric"] = str(num_sal) if num_sal is not None else ""
        else:
            clean_row["salary_numeric"] = ""

        if "hire_date" in clean_row and clean_row["hire_date"]:
            clean_row["hire_date"] = standardize_date_safely(clean_row["hire_date"])

        # Check email format without inventing missing email
        if "email" in clean_row and clean_row["email"]:
            clean_row["email"] = clean_row["email"].lower()
            if not EMAIL_REGEX.match(clean_row["email"]):
                report["invalid_email_count"] += 1

        cleaned_records.append(clean_row)

    # 3. Detect Duplicate Employee Records (by employee_id)
    seen_employee_ids = set()
    deduped_records: List[Dict[str, Any]] = []

    for r in cleaned_records:
        emp_id = r.get("employee_id", "").strip()
        if emp_id:
            if emp_id in seen_employee_ids:
                report["duplicate_records"] += 1
                report["duplicate_employee_ids"].append(emp_id)
                continue
            seen_employee_ids.add(emp_id)
        deduped_records.append(r)

    # 4. Validate Required Employee Fields & Separate Valid vs Invalid
    valid_records: List[Dict[str, Any]] = []
    invalid_records: List[Dict[str, Any]] = []

    # Initialize missing fields tracker for all present columns
    canonical_columns = list(dict.fromkeys(rename_map.values()))
    for col in canonical_columns:
        report["missing_fields"][col] = 0

    for r in deduped_records:
        missing_in_row = []
        for req_field in required_fields:
            if not r.get(req_field) or str(r.get(req_field)).strip() == "":
                missing_in_row.append(req_field)

        # Track missing values across all columns (Do not invent data!)
        for col in canonical_columns:
            if not r.get(col) or str(r.get(col)).strip() == "":
                report["missing_fields"][col] += 1

        if missing_in_row:
            r_copy = dict(r)
            r_copy["validation_error"] = f"Missing required fields: {', '.join(missing_in_row)}"
            invalid_records.append(r_copy)
            report["invalid_records"] += 1
        else:
            valid_records.append(r)
            report["valid_records"] += 1

    # 5. Convert back to pandas DataFrame if pandas is installed
    if is_pandas:
        import pandas as pd
        valid_df = pd.DataFrame(valid_records) if valid_records else pd.DataFrame(columns=canonical_columns)
        invalid_df = pd.DataFrame(invalid_records) if invalid_records else pd.DataFrame()
    else:
        valid_df = valid_records
        invalid_df = invalid_records

    return valid_df, invalid_df, report


def save_cleaned_data(
    valid_data,
    output_excel: Path,
    output_csv: Path
):
    """Saves cleaned and validated employee data to both Excel and CSV formats."""
    output_excel.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd
        if isinstance(valid_data, pd.DataFrame):
            valid_data.to_excel(output_excel, index=False, engine="openpyxl")
            valid_data.to_csv(output_csv, index=False, encoding="utf-8")
            print(f"[OK] Cleaned Excel saved to: {output_excel.resolve()}")
            print(f"[OK] Cleaned CSV saved to:   {output_csv.resolve()}")
            return
    except ImportError:
        pass

    # Standard library fallback
    import csv
    import openpyxl

    records = valid_data if isinstance(valid_data, list) else valid_data.to_dict(orient="records")
    if not records:
        print("[!] Warning: Valid records list is empty.")
        return

    fields = list(records[0].keys())

    # Write CSV
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"[OK] Cleaned CSV saved to:   {output_csv.resolve()}")

    # Write Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(fields)
    for r in records:
        ws.append([r.get(f, "") for f in fields])
    wb.save(str(output_excel))
    print(f"[OK] Cleaned Excel saved to: {output_excel.resolve()}")


def print_terminal_summary(report: Dict[str, Any], input_path: Path, output_excel: Path, output_csv: Path):
    """Prints a structured, executive terminal report detailing data quality and validation stats."""
    print("\n" + "=" * 65)
    print("       STAGE 2: DATA CLEANING & VALIDATION SUMMARY")
    print("=" * 65)
    print(f"Source Input File:        {input_path.name} ({input_path.resolve()})")
    print(f"Total Records Ingested:   {report['total_records']}")
    print(f"Empty Rows Removed:       {report['empty_rows_removed']}")
    print(f"Exact Duplicate Rows:     {report['exact_duplicates_removed']}")
    print(f"Duplicate Employee IDs:   {report['duplicate_records']}")
    if report['duplicate_employee_ids']:
        sample_dup = report['duplicate_employee_ids'][:5]
        print(f"     [!] Duplicate IDs found: {', '.join(sample_dup)}{'...' if len(report['duplicate_employee_ids']) > 5 else ''}")
    print(f"Invalid Records Flagged:  {report['invalid_records']}")
    print(f"Valid Cleaned Records:    {report['valid_records']}")
    print("-" * 65)

    print("Missing Field Breakdown (Data Integrity - No Invented Data):")
    missing_items = sorted(report["missing_fields"].items(), key=lambda x: x[1], reverse=True)
    for field, count in missing_items:
        status_tag = f"({count} missing)" if count > 0 else "(Complete - 0 missing)"
        print(f"   - {field:<24} {status_tag}")

    if report["invalid_email_count"] > 0:
        print(f"   - Invalid email format:    {report['invalid_email_count']} flagged")

    print("-" * 65)
    print(f"Cleaned Excel Output:     {output_excel.resolve()}")
    print(f"Cleaned CSV Output:       {output_csv.resolve()}")
    print("Status:                   SUCCESS [OK]")
    print("=" * 65 + "\n")


def clean_and_validate_employee_data(
    input_path: Path,
    output_excel: Path,
    output_csv: Path,
    required_fields: Optional[List[str]] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Main pipeline entrypoint for Stage 2:
    Loads extracted data, cleans whitespace, removes empty/duplicate rows,
    validates required fields without inventing fake data, saves outputs,
    and displays summary report in terminal.
    """
    print(f"[*] Loading extracted data from: {input_path}")
    raw_df = load_input_data(input_path)

    valid_df, invalid_df, report = clean_and_validate_dataframe(raw_df, required_fields=required_fields)

    save_cleaned_data(valid_df, output_excel, output_csv)
    print_terminal_summary(report, input_path, output_excel, output_csv)

    return valid_df, report


def main():
    parser = argparse.ArgumentParser(
        description="Clean, validate, and standardize employee data without fabricating missing info.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "employees.xlsx",
        help="Path to extracted Excel file (default: data/employees.xlsx)"
    )
    parser.add_argument(
        "--output-excel", "-x",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "cleaned_employees.xlsx",
        help="Destination path for cleaned Excel file (default: data/cleaned_employees.xlsx)"
    )
    parser.add_argument(
        "--output-csv", "-c",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "cleaned_employees.csv",
        help="Destination path for cleaned CSV file (default: data/cleaned_employees.csv)"
    )
    parser.add_argument(
        "--required-fields", "-r",
        nargs="+",
        default=DEFAULT_REQUIRED_FIELDS,
        help="List of required fields for an employee record to be considered valid."
    )
    args = parser.parse_args()

    print("\n=================================================================")
    print("    STAGE 2: DATA CLEANING AND VALIDATION")
    print("=================================================================\n")

    try:
        clean_and_validate_employee_data(
            input_path=args.input,
            output_excel=args.output_excel,
            output_csv=args.output_csv,
            required_fields=args.required_fields
        )
    except Exception as e:
        print(f"\n[DATA CLEANING ERROR]: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
