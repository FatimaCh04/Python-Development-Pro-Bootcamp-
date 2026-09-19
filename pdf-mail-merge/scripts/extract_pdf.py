"""
PDF Employee Data Extraction Engine
Extracts employee records from multi-page PDF documents.

Key Capabilities:
1. Detects document characteristics:
   - Selectable text / tables
   - Structured bordered tables
   - Scanned / image pages
2. Extraction Methods:
   - Primary: pdfplumber for text and multi-page table extraction
   - Secondary: Camelot (lattice & stream) for structured tables
   - Fallback: OCR (pytesseract + pdf2image) for scanned / image PDFs
3. Data Post-Processing:
   - Strips blank rows and repeated headers across pages
   - Returns structured pandas DataFrame
   - Saves to data/employees.xlsx and data/employees.csv
4. Robust Error Handling:
   - Missing PDF file
   - Unreadable / corrupted / encrypted PDF
   - No tables or records found
   - OCR engine / dependencies unavailable
   - Empty extraction
"""

import sys
import os
import re
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Custom Exceptions for Granular Error Handling
class PDFExtractionError(Exception):
    """Base exception for PDF extraction failures."""
    pass

class MissingPDFError(PDFExtractionError):
    """Raised when the specified input PDF file does not exist."""
    pass

class UnreadablePDFError(PDFExtractionError):
    """Raised when the PDF file cannot be opened or parsed."""
    pass

class NoTablesFoundError(PDFExtractionError):
    """Raised when no tabular data could be discovered."""
    pass

class OCRError(PDFExtractionError):
    """Raised when OCR is requested or needed but prerequisites are unavailable."""
    pass

class EmptyExtractionError(PDFExtractionError):
    """Raised when extraction executes but returns zero records."""
    pass


def detect_pdf_type(pdf_path: Path) -> Dict[str, Any]:
    """
    Analyzes the PDF to determine whether it contains:
    - 'STRUCTURED_TABLES': Explicit table lines, grids, or borders
    - 'SELECTABLE_TEXT': Digital text streams and characters
    - 'SCANNED_IMAGES': Minimal text with raster image content
    """
    import pdfplumber

    total_pages = 0
    total_characters = 0
    total_tables = 0
    total_images = 0
    has_lines_or_rects = False

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            total_pages = len(pdf.pages)
            if total_pages == 0:
                raise UnreadablePDFError(f"PDF at '{pdf_path}' has 0 pages.")

            # Sample up to first 5 pages for classification
            sample_pages = pdf.pages[:min(5, total_pages)]
            for page in sample_pages:
                text = page.extract_text() or ""
                total_characters += len(text.strip())

                # Check for table objects
                tables = page.find_tables()
                if tables:
                    total_tables += len(tables)

                # Check for vector lines or bounding rectangles indicating grid tables
                if (hasattr(page, "lines") and len(page.lines) > 4) or (hasattr(page, "rects") and len(page.rects) > 4):
                    has_lines_or_rects = True

                # Check for embedded raster images
                if hasattr(page, "images") and len(page.images) > 0:
                    total_images += len(page.images)

    except Exception as e:
        if isinstance(e, PDFExtractionError):
            raise
        raise UnreadablePDFError(f"Could not read PDF '{pdf_path}': {e}") from e

    # Classification logic
    avg_chars_per_page = total_characters / max(1, len(sample_pages))

    if total_tables > 0 or has_lines_or_rects:
        pdf_type = "STRUCTURED_TABLES"
        description = "Contains structured tables with grid/line formatting"
    elif avg_chars_per_page > 50:
        pdf_type = "SELECTABLE_TEXT"
        description = "Contains selectable digital text streams"
    elif total_images > 0 and avg_chars_per_page <= 50:
        pdf_type = "SCANNED_IMAGES"
        description = "Scanned / image-based document (requires OCR)"
    else:
        pdf_type = "UNKNOWN"
        description = "Indeterminate format or minimal content"

    return {
        "type": pdf_type,
        "description": description,
        "total_pages": total_pages,
        "sample_char_count": total_characters,
        "tables_detected": total_tables,
        "has_grid_lines": has_lines_or_rects,
        "has_images": total_images > 0
    }


def extract_with_camelot(pdf_path: Path) -> List[List[str]]:
    """
    Extracts structured tables using camelot-py when installed.
    Tries lattice flavor first (for bordered grids), then stream flavor.
    """
    try:
        import camelot
    except ImportError:
        print("[!] camelot-py is not installed. Falling back to pdfplumber...")
        return []

    print("[*] Running Camelot extraction on structured tables...")
    try:
        # Try lattice mode for explicit line tables
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")
        if len(tables) == 0:
            print("[*] No lattice tables found. Trying Camelot stream flavor...")
            tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")

        if len(tables) > 0:
            all_rows = []
            header = None
            for table in tables:
                t_df = table.df
                if t_df.empty:
                    continue
                rows = t_df.values.tolist()
                for row in rows:
                    cleaned_row = [str(c).strip() for c in row]
                    if not any(cleaned_row):
                        continue
                    if header is None:
                        header = cleaned_row
                        all_rows.append(header)
                    else:
                        # Check for repeated header
                        if [c.lower() for c in cleaned_row] != [c.lower() for c in header]:
                            all_rows.append(cleaned_row)
            return all_rows

    except Exception as e:
        print(f"[!] Camelot extraction warning: {e}. Falling back to pdfplumber.")

    return []


def extract_with_pdfplumber(pdf_path: Path) -> List[List[str]]:
    """
    Extracts tabular employee data across all pages using pdfplumber.
    Handles multi-page rosters, repeated headers, and multiline table cells.
    """
    import pdfplumber

    all_rows: List[List[str]] = []
    header: Optional[List[str]] = None

    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)

        for page_idx, page in enumerate(pdf.pages, start=1):
            # Attempt 1: Default table extraction
            tables = page.extract_tables()

            # Attempt 2: If default found nothing, try explicit edge & text strategies
            if not tables:
                tables = page.extract_tables({
                    "vertical_strategy": "text",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 4,
                    "join_tolerance": 4,
                })

            if not tables:
                # Attempt 3: Line-based vertical strategy
                tables = page.extract_tables({
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                })

            if tables:
                for table in tables:
                    if not table:
                        continue

                    # Filter out empty rows and clean cell text
                    for raw_row in table:
                        if not raw_row:
                            continue
                        clean_row = [
                            re.sub(r"\s+", " ", cell.replace("\n", " ")).strip() if cell else ""
                            for cell in raw_row
                        ]

                        # Skip row if all cells are blank
                        if not any(clean_row):
                            continue

                        if header is None:
                            # First valid row becomes our header
                            header = [c if c else f"Column_{i+1}" for i, c in enumerate(clean_row)]
                            all_rows.append(header)
                        else:
                            # Skip repeated header row
                            if [c.lower() for c in clean_row] == [c.lower() for c in header]:
                                continue

                            # Standardize row length to match header
                            if len(clean_row) < len(header):
                                clean_row += [""] * (len(header) - len(clean_row))
                            elif len(clean_row) > len(header):
                                clean_row = clean_row[:len(header)]

                            all_rows.append(clean_row)

            else:
                # Text-based line parsing fallback if no tables extracted
                text = page.extract_text()
                if text:
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        # Detect delimiters like tabs, commas, or pipes
                        for delim in ["\t", "|", ","]:
                            if delim in line and line.count(delim) >= 3:
                                parts = [p.strip() for p in line.split(delim)]
                                if header is None:
                                    header = parts
                                    all_rows.append(header)
                                else:
                                    if [p.lower() for p in parts] != [p.lower() for p in header]:
                                        all_rows.append(parts)
                                break

    return all_rows


def extract_with_ocr(pdf_path: Path) -> List[List[str]]:
    """
    OCR extraction engine for scanned or image-only PDF documents
    using pytesseract and pdf2image.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError as e:
        raise OCRError(
            "OCR extraction requested for scanned PDF, but 'pytesseract' or 'pdf2image' "
            "is not installed. Please run: pip install pytesseract pdf2image Pillow"
        ) from e

    print("[*] Running OCR on scanned PDF pages...")
    try:
        images = convert_from_path(str(pdf_path), dpi=300)
    except Exception as e:
        raise OCRError(
            f"Failed converting PDF pages to images. Ensure Poppler is installed and in PATH.\n"
            f"Details: {e}"
        ) from e

    all_rows: List[List[str]] = []
    header: Optional[List[str]] = None

    for idx, img in enumerate(images, start=1):
        print(f"  [OCR] Scanning page {idx}/{len(images)}...")
        try:
            tsv_data = pytesseract.image_to_string(img)
        except Exception as e:
            raise OCRError(
                f"Tesseract OCR failed to process image. Ensure Tesseract OCR engine is installed.\n"
                f"Details: {e}"
            ) from e

        lines = [line.strip() for line in tsv_data.splitlines() if line.strip()]
        for line in lines:
            # Check for delimiters or whitespace separated tabular data
            if "\t" in line:
                parts = [p.strip() for p in line.split("\t")]
            elif "|" in line:
                parts = [p.strip() for p in line.split("|")]
            elif "," in line and line.count(",") >= 3:
                parts = [p.strip() for p in line.split(",")]
            else:
                parts = [p.strip() for p in re.split(r"\s{2,}", line) if p.strip()]

            if len(parts) >= 3:
                if header is None:
                    header = parts
                    all_rows.append(header)
                else:
                    if [p.lower() for p in parts] != [p.lower() for p in header]:
                        all_rows.append(parts)

    return all_rows


def save_tabular_data(raw_rows: List[List[str]], csv_path: Path, excel_path: Path) -> Tuple[Any, List[str]]:
    """
    Converts extracted row records into tabular CSV and Excel files,
    using pandas if available or pure Python csv/openpyxl as fallback.
    """
    if not raw_rows or len(raw_rows) <= 1:
        raise EmptyExtractionError("No data rows were extracted from the PDF.")

    header = raw_rows[0]
    data_rows = raw_rows[1:]

    # Remove any stray empty rows or header duplicates in data
    cleaned_data_rows = []
    for row in data_rows:
        # Standardize length
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[:len(header)]

        # Skip empty or duplicate header
        if not any(c.strip() for c in row):
            continue
        if [c.lower().strip() for c in row] == [c.lower().strip() for c in header]:
            continue

        cleaned_data_rows.append(row)

    if not cleaned_data_rows:
        raise EmptyExtractionError("Extraction completed but all extracted rows were empty or headers.")

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    excel_path.parent.mkdir(parents=True, exist_ok=True)

    # Try pandas
    try:
        import pandas as pd
        df = pd.DataFrame(cleaned_data_rows, columns=header)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_excel(excel_path, index=False, engine="openpyxl")
        return df, header

    except ImportError:
        # Graceful fallback to standard library csv + openpyxl
        print("[*] pandas not imported; using standard csv & openpyxl...")
        # Write CSV
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(cleaned_data_rows)

        # Write Excel
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(header)
            for r in cleaned_data_rows:
                ws.append(r)
            wb.save(str(excel_path))
        except Exception as e:
            print(f"[!] Note: Excel file could not be created: {e}")

        # Return a lightweight proxy or list
        class DictProxy:
            def __init__(self, rows, cols):
                self.columns = cols
                self._rows = rows
            def __len__(self):
                return len(self._rows)

        return DictProxy(cleaned_data_rows, header), header


def extract_employee_records(
    pdf_path: Path,
    output_csv: Path,
    output_excel: Path
) -> Tuple[Any, Dict[str, Any]]:
    """
    Main extraction orchestrator:
    1. Validates input PDF
    2. Detects content type (Structured, Selectable Text, Scanned)
    3. Selects optimal extraction engine (Camelot, pdfplumber, or OCR)
    4. Cleans empty rows and duplicate headers
    5. Saves to CSV and Excel
    6. Displays comprehensive status report in terminal
    """
    if not pdf_path.exists():
        raise MissingPDFError(
            f"Input PDF file not found at: '{pdf_path}'.\n"
            f"Please place your real employee PDF inside the 'input/' directory as 'employees.pdf'."
        )

    if pdf_path.stat().st_size == 0:
        raise UnreadablePDFError(f"Input PDF '{pdf_path}' is an empty 0-byte file.")

    # 1. Detection Phase
    detection = detect_pdf_type(pdf_path)
    total_pages = detection["total_pages"]
    pdf_type = detection["type"]

    print(f"[*] PDF Inspection: {total_pages} page(s) detected.")
    print(f"[*] Document Classification: {pdf_type} ({detection['description']})")

    raw_rows: List[List[str]] = []
    engine_used = ""

    # 2. Selection & Extraction Phase
    if pdf_type == "STRUCTURED_TABLES":
        # First attempt Camelot if available, else pdfplumber
        raw_rows = extract_with_camelot(pdf_path)
        if raw_rows:
            engine_used = "Camelot"
        else:
            raw_rows = extract_with_pdfplumber(pdf_path)
            engine_used = "pdfplumber"

    elif pdf_type == "SELECTABLE_TEXT":
        raw_rows = extract_with_pdfplumber(pdf_path)
        engine_used = "pdfplumber"

    elif pdf_type == "SCANNED_IMAGES":
        raw_rows = extract_with_ocr(pdf_path)
        engine_used = "pytesseract / pdf2image (OCR)"

    else:
        # Fallback sequence: pdfplumber -> Camelot -> OCR
        raw_rows = extract_with_pdfplumber(pdf_path)
        if raw_rows:
            engine_used = "pdfplumber"
        else:
            raw_rows = extract_with_camelot(pdf_path)
            if raw_rows:
                engine_used = "Camelot"
            else:
                raw_rows = extract_with_ocr(pdf_path)
                engine_used = "pytesseract / pdf2image (OCR)"

    if not raw_rows:
        raise NoTablesFoundError(
            f"No employee tables or records could be detected in '{pdf_path}'.\n"
            f"Check if the PDF has text content, or if scanned, ensure Tesseract & Poppler are installed."
        )

    # 3. Clean obvious empty rows & duplicate headers, save outputs
    df_or_proxy, detected_columns = save_tabular_data(raw_rows, output_csv, output_excel)
    record_count = len(df_or_proxy)

    summary = {
        "pdf_path": str(pdf_path),
        "total_pages": total_pages,
        "pdf_type": pdf_type,
        "engine_used": engine_used,
        "record_count": record_count,
        "detected_columns": detected_columns,
        "output_csv": str(output_csv),
        "output_excel": str(output_excel),
        "success": True
    }

    # 4. Terminal Display
    print("\n" + "=" * 65)
    print("           PDF EXTRACTION SUMMARY REPORT")
    print("=" * 65)
    print(f"Source PDF:             {pdf_path.name} ({pdf_path.resolve()})")
    print(f"Total PDF Pages:        {total_pages}")
    print(f"Document Type:          {pdf_type}")
    print(f"Extraction Engine Used: {engine_used}")
    print(f"Extracted Records:      {record_count}")
    print(f"Detected Columns ({len(detected_columns)}):")
    for idx, col in enumerate(detected_columns, start=1):
        print(f"   {idx}. {col}")
    print("-" * 65)
    print(f"CSV Output:             {output_csv.resolve()}")
    print(f"Excel Output:           {output_excel.resolve()}")
    print("Status:                 SUCCESS [OK]")
    print("=" * 65 + "\n")

    return df_or_proxy, summary


def main():
    parser = argparse.ArgumentParser(
        description="Extract employee records from PDF to tabular CSV and Excel.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "input" / "employees.pdf",
        help="Path to employee source PDF"
    )
    parser.add_argument(
        "--output-csv", "-c",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "employees.csv",
        help="Path for output CSV"
    )
    parser.add_argument(
        "--output-excel", "-x",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "employees.xlsx",
        help="Path for output Excel"
    )
    args = parser.parse_args()

    print("\n=================================================================")
    print("    STAGE 1: PDF EMPLOYEE DATA EXTRACTION")
    print("=================================================================\n")

    try:
        extract_employee_records(
            pdf_path=args.input,
            output_csv=args.output_csv,
            output_excel=args.output_excel
        )
    except MissingPDFError as e:
        print(f"\n[ERROR: MISSING PDF]\n{e}\n", file=sys.stderr)
        sys.exit(1)
    except UnreadablePDFError as e:
        print(f"\n[ERROR: UNREADABLE PDF]\n{e}\n", file=sys.stderr)
        sys.exit(1)
    except NoTablesFoundError as e:
        print(f"\n[ERROR: NO TABLES FOUND]\n{e}\n", file=sys.stderr)
        sys.exit(1)
    except OCRError as e:
        print(f"\n[ERROR: OCR UNAVAILABLE]\n{e}\n", file=sys.stderr)
        sys.exit(1)
    except EmptyExtractionError as e:
        print(f"\n[ERROR: EMPTY EXTRACTION]\n{e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[UNEXPECTED EXTRACTION ERROR]: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
