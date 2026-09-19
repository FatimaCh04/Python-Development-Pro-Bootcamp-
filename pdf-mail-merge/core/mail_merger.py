import pandas as pd
from pathlib import Path
from typing import Dict, Any, Callable
import re
from datetime import datetime

class MailMergeError(Exception): pass

def sanitize_filename(text: str) -> str:
    cleaned = re.sub(r'[\\/\*\?:"<>|\x00-\x1f\x7f]', "", str(text))
    cleaned = re.sub(r"[\s\-\.]+", "_", cleaned)
    return cleaned.strip("._")[:60]

def unique_output_path(directory: Path, stem: str) -> Path:
    candidate = directory / f"{stem}.docx"
    if not candidate.exists():
        return candidate
    counter = 2
    while True:
        candidate = directory / f"{stem}_v{counter}.docx"
        if not candidate.exists():
            return candidate
        counter += 1

def generate_documents(df: pd.DataFrame, template_path: Path, output_dir: Path, progress_callback: Callable = None) -> Dict[str, Any]:
    """
    Generates Word documents from the dataframe.
    progress_callback signature: cb(current_index, total_records, employee_name, status_msg)
    """
    try:
        from docxtpl import DocxTemplate
    except ImportError:
        raise MailMergeError("docxtpl is not installed.")
        
    if not template_path.exists():
        raise MailMergeError(f"Template not found at {template_path}")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total = len(df)
    success_count = 0
    failed_count = 0
    failed_records = []
    
    records = df.to_dict(orient="records")
    
    for idx, row in enumerate(records, start=1):
        emp_id = str(row.get('employee_id', f'EMP{idx:04d}'))
        emp_name = str(row.get('full_name', f'Unknown_{idx}'))
        
        if progress_callback:
            progress_callback(idx, total, emp_name, "Processing...")
            
        try:
            # Build context
            context = {k: str(v) for k, v in row.items()}
            context['current_date'] = datetime.now().strftime("%B %d, %Y")
            
            # Render
            doc = DocxTemplate(str(template_path))
            doc.render(context)
            
            # Save
            stem = f"Employee_{sanitize_filename(emp_id)}"
            out_path = unique_output_path(output_dir, stem)
            doc.save(str(out_path))
            
            success_count += 1
            if progress_callback:
                progress_callback(idx, total, emp_name, "Success")
                
        except Exception as e:
            failed_count += 1
            failed_records.append({"id": emp_id, "name": emp_name, "error": str(e)})
            if progress_callback:
                progress_callback(idx, total, emp_name, f"Failed: {e}")
                
    return {
        "total": total,
        "success": success_count,
        "failed": failed_count,
        "failed_records": failed_records
    }
