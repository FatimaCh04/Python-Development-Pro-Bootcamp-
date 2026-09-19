# PDF Employee Data to Automated Mail Merge System

## PROJECT PURPOSE
The purpose of this project is to automate the extraction of employee data from a PDF document, clean and validate the extracted data, and generate personalized Word (.docx) and PDF documents for each employee through an automated mail merge pipeline.

## PROBLEM STATEMENT
Manually typing or copying employee information from unformatted PDF reports into individual corporate documents is highly repetitive, prone to human error, and time-consuming. There is a need for a reliable, offline, script-based system that can bridge the gap between unstructured PDF reports and standardized corporate documents.

## SOLUTION
This Python automation pipeline solves the problem by chaining together four distinct processing stages:
1. **Extraction:** Intelligently reading tabular data from a PDF using multi-engine extraction (pdfplumber, camelot, pytesseract).
2. **Cleansing:** Standardizing headers, removing blank/duplicate rows, and validating required fields without inventing fake data.
3. **Mail Merge:** Dynamically matching Excel columns to Jinja variables in a Word template to generate individualized documents.
4. **Conversion:** Automatically batch-converting generated Word documents into final PDFs via LibreOffice's headless CLI.

## TECHNOLOGY USED
* **Python 3**
* **pandas** (Data manipulation and validation)
* **pdfplumber** / **Camelot** (PDF table and text extraction)
* **openpyxl** (Excel fallback integration)
* **docxtpl** / **python-docx** (Jinja2-based Word document rendering)
* **pytesseract** / **pdf2image** (Optional OCR support)
* **LibreOffice** (Headless DOCX to PDF conversion)

## PROJECT STRUCTURE
```text
pdf-mail-merge/
│
├── input/
│   └── employees.pdf                 <-- Place your source PDF here
│
├── data/
│   ├── employees.csv                 <-- Raw extracted data
│   ├── employees.xlsx                <-- Raw extracted data
│   ├── cleaned_employees.csv         <-- Validated data
│   └── cleaned_employees.xlsx        <-- Validated data
│
├── templates/
│   └── employee_template.docx        <-- Word template with Jinja tags
│
├── output/
│   ├── word/                         <-- Generated Word files saved here
│   └── pdf/                          <-- Converted PDFs saved here
│
├── scripts/
│   ├── __init__.py
│   ├── extract_pdf.py                (Stage 1)
│   ├── clean_data.py                 (Stage 2)
│   ├── mail_merge.py                 (Stage 3)
│   ├── convert_to_pdf.py             (Stage 4)
│   ├── create_sample_template.py     (Template Generator)
│   └── main.py                       (Master Orchestrator)
│
├── requirements.txt
└── README.md
```

## INSTALLATION STEPS
To set up this Python automation project locally, run the following exact commands in your terminal:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## WINDOWS SETUP
1. **Python Environment:** Ensure Python 3.8+ is installed and added to your `PATH`.
2. **LibreOffice (Required for PDF Conversion):** 
   You must install LibreOffice to enable the automated DOCX to PDF conversion. Open your terminal and run:
   ```bash
   winget install TheDocumentFoundation.LibreOffice
   ```
   *(Alternatively, download and install it manually from libreoffice.org).*

## HOW TO ADD THE PDF
1. Ensure your PDF document contains the employee records.
2. Rename the file to **`employees.pdf`**.
3. Place the file exactly at:
   ```
   input/employees.pdf
   ```
*(Note: The system will gracefully halt and warn you if this file is missing. It will never generate fake employee records).*

## HOW TO ADD/EDIT THE WORD TEMPLATE
1. The mail merge requires a Microsoft Word document containing Jinja2 template tags (e.g., `{{ employee_id }}`, `{{ full_name }}`).
2. Place your Word document exactly at:
   ```
   templates/employee_template.docx
   ```
3. **Dynamic Variables:** Any column header present in your extracted Excel data can be used directly as a variable inside the template by wrapping it in double curly braces. 
*(Note: If the template is missing, the script will automatically generate a professional default sample template for you).*

## HOW TO RUN THE PROJECT
Once your PDF and Template are in place, trigger the master orchestrator to run the entire pipeline end-to-end:

```bash
python scripts/main.py
```

## EXPECTED OUTPUT
When executed successfully, the terminal will display a clear, step-by-step progress tracker followed by a final metric summary:

```text
========================================
PDF EMPLOYEE MAIL MERGE AUTOMATION
==================================

[1/5] Checking PDF...
[2/5] Extracting employee data...
[3/5] Cleaning and validating data...
[4/5] Generating employee documents...
[5/5] Converting documents to PDF...

========================================
PROCESS COMPLETED
=================

* PDF pages: 3
* extracted records: 200
* valid records: 198
* invalid records: 2
* generated DOCX count: 198
* generated PDF count: 198
* failed records: 0
* output locations: 
    - Word docs: C:\...\pdf-mail-merge\output\word
    - PDF docs:  C:\...\pdf-mail-merge\output\pdf
```

## TROUBLESHOOTING
* **Extraction Errors / No Tables Found:** If the PDF is heavily scanned, ensure you have installed Tesseract OCR and Poppler. Alternatively, check if the PDF is encrypted/password-protected.
* **Mail Merge Failures / Blank Files:** Verify that the column names in your PDF/Excel sheet exactly match the variables you typed into the Word template. 
* **PDF Conversion Skips:** If you receive a "LIBREOFFICE NOT DETECTED" warning, double-check your LibreOffice installation and ensure `soffice.exe` is available. Your `.docx` files will still be safely generated in `output/word/`.

## EXAMPLE COMMANDS
Run the full pipeline:
```bash
python scripts/main.py
```

Run only a specific stage (useful for testing):
```bash
python scripts/main.py --step extract
python scripts/main.py --step clean
python scripts/main.py --step merge
python scripts/main.py --step convert
```

Process only the first 5 records (quick testing):
```bash
python scripts/main.py --limit 5
```
