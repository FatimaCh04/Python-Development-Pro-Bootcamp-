import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
import shutil
import re

class ExtractionError(Exception): pass

def extract_pdf_data(pdf_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Extracts tabular data from the PDF using pdfplumber as the robust default."""
    if not pdf_path.exists():
        raise ExtractionError("PDF file not found.")
        
    try:
        import pdfplumber
    except ImportError:
        raise ExtractionError("pdfplumber is required for extraction.")

    all_rows = []
    total_pages = 0
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        for page in pdf.pages:
            tables = page.extract_tables(table_settings={"vertical_strategy": "lines", "horizontal_strategy": "lines"})
            if not tables:
                tables = page.extract_tables(table_settings={"vertical_strategy": "text", "horizontal_strategy": "text"})
            
            for table in tables:
                for row in table:
                    clean_row = [str(cell).strip() if cell else "" for cell in row]
                    # Filter out purely empty rows
                    if any(clean_row):
                        # Replace newlines within cells
                        clean_row = [re.sub(r'\s+', ' ', cell) for cell in clean_row]
                        all_rows.append(clean_row)
                        
    if not all_rows:
        raise ExtractionError("No tabular data could be found in the PDF.")
        
    # Assume first non-empty row is header
    header = all_rows[0]
    data_rows = all_rows[1:]
    
    # Remove repeated headers
    data_rows = [r for r in data_rows if r != header]
    
    df = pd.DataFrame(data_rows, columns=header)
    
    summary = {
        "total_pages": total_pages,
        "record_count": len(df),
        "columns": header
    }
    
    return df, summary
