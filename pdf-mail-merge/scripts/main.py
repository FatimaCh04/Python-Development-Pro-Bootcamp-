"""
Master Pipeline Orchestrator

Executes the entire PDF to Mail Merge automation sequence:
STEP 1: Check PDF input
STEP 2: Extract data
STEP 3: Save to Excel/CSV (Handled inside extract)
STEP 4: Clean and validate
STEP 5: Generate DOCX
STEP 6: Convert to PDF
STEP 7: Generate Report
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure local modules can be imported
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from extract_pdf import extract_employee_records, PDFExtractionError
from clean_data import clean_and_validate_employee_data
from mail_merge import generate_mail_merge
from convert_to_pdf import convert_word_to_pdf
from create_sample_template import create_employee_template


def main():
    parser = argparse.ArgumentParser(description="PDF Employee Mail Merge Automation")
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Optional limit on records processed for testing."
    )
    args = parser.parse_args()

    # Define all paths
    input_pdf = PROJECT_DIR / "input" / "employees.pdf"
    extracted_csv = PROJECT_DIR / "data" / "employees.csv"
    extracted_excel = PROJECT_DIR / "data" / "employees.xlsx"
    clean_csv = PROJECT_DIR / "data" / "cleaned_employees.csv"
    clean_excel = PROJECT_DIR / "data" / "cleaned_employees.xlsx"
    template_path = PROJECT_DIR / "templates" / "employee_template.docx"
    word_dir = PROJECT_DIR / "output" / "word"
    pdf_dir = PROJECT_DIR / "output" / "pdf"

    print("\n========================================")
    print("PDF EMPLOYEE MAIL MERGE AUTOMATION")
    print("==================================\n")

    # Metrics dictionary to populate throughout the pipeline
    metrics = {
        "pdf_pages": 0,
        "extracted_records": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "generated_docx": 0,
        "generated_pdf": 0,
        "failed_records": 0,
        "output_word_dir": str(word_dir.resolve()),
        "output_pdf_dir": str(pdf_dir.resolve()),
    }

    try:
        # STEP 1: Check input/employees.pdf exists.
        print("[1/5] Checking PDF...")
        if not input_pdf.exists():
            print(f"[!] ERROR: Input PDF not found at {input_pdf}")
            print("Please place the source PDF in the input/ folder.")
            sys.exit(1)

        # STEP 2 & 3: Extract employee data and save as Excel/CSV
        print("[2/5] Extracting employee data...")
        # Check if directories exist
        extracted_csv.parent.mkdir(parents=True, exist_ok=True)
        _, extract_summary = extract_employee_records(
            pdf_path=input_pdf,
            output_csv=extracted_csv,
            output_excel=extracted_excel
        )
        metrics["pdf_pages"] = extract_summary.get("total_pages", 0)
        metrics["extracted_records"] = extract_summary.get("total_records", 0)  # wait, it was record_count

        # Get exact key for extracted records just in case
        if "record_count" in extract_summary:
            metrics["extracted_records"] = extract_summary["record_count"]
        elif "total_records" in extract_summary:
            metrics["extracted_records"] = extract_summary["total_records"]
        elif "sample_char_count" in extract_summary: 
            # safe fallback if the dict structure differs slightly
            metrics["extracted_records"] = extract_summary.get("extracted_records", extract_summary.get("record_count", 0))

        # STEP 4: Clean and validate employee data
        print("[3/5] Cleaning and validating data...")
        clean_input = extracted_excel if extracted_excel.exists() else extracted_csv
        _, clean_report = clean_and_validate_employee_data(
            input_path=clean_input,
            output_excel=clean_excel,
            output_csv=clean_csv
        )
        metrics["valid_records"] = clean_report.get("valid_records", 0)
        metrics["invalid_records"] = clean_report.get("invalid_records", 0)
        # fallback in case clean report doesn't contain valid_records but rather total minus invalid
        if metrics["extracted_records"] == 0 and "total_records" in clean_report:
            metrics["extracted_records"] = clean_report["total_records"]

        # STEP 5: Generate personalized DOCX documents
        print("[4/5] Generating employee documents...")
        if not template_path.exists():
            # Generate default template if missing
            create_employee_template(template_path)

        merge_input = clean_excel if clean_excel.exists() else clean_csv
        merge_result = generate_mail_merge(
            data_path=merge_input,
            template_path=template_path,
            output_dir=word_dir,
            limit=args.limit
        )
        
        metrics["generated_docx"] = merge_result.get("success", 0)
        metrics["failed_records"] = merge_result.get("failed", 0)

        # STEP 6: Convert generated DOCX files to PDF
        print("[5/5] Converting documents to PDF...")
        converted_count = convert_word_to_pdf(
            input_path=word_dir,
            output_dir=pdf_dir,
            limit=args.limit
        )
        metrics["generated_pdf"] = converted_count

        # STEP 7: Generate Final Report
        print("\n========================================")
        print("PROCESS COMPLETED")
        print("=================\n")

        print(f"* PDF pages: {metrics['pdf_pages']}")
        print(f"* extracted records: {metrics['extracted_records']}")
        print(f"* valid records: {metrics['valid_records']}")
        print(f"* invalid records: {metrics['invalid_records']}")
        print(f"* generated DOCX count: {metrics['generated_docx']}")
        print(f"* generated PDF count: {metrics['generated_pdf']}")
        print(f"* failed records: {metrics['failed_records']}")
        print(f"* output locations: ")
        print(f"    - Word docs: {metrics['output_word_dir']}")
        print(f"    - PDF docs:  {metrics['output_pdf_dir']}\n")

    except Exception as e:
        print(f"\n[!] A fatal pipeline error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
