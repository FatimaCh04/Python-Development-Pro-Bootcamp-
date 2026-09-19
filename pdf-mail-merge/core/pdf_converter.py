import sys
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

def find_libreoffice() -> Optional[str]:
    for cmd in ["soffice", "libreoffice"]:
        found = shutil.which(cmd)
        if found:
            return found

    if sys.platform.startswith("win"):
        candidate_paths = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "LibreOffice" / "program" / "soffice.exe",
        ]
        for p in candidate_paths:
            if p.is_file():
                return str(p)
    return None

def convert_to_pdf_batch(input_dir: Path, output_dir: Path, progress_callback: Callable = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    
    docx_files = sorted(list(input_dir.glob("*.docx")))
    total = len(docx_files)
    
    if total == 0:
        return {"total": 0, "success": 0, "failed": 0, "error": "No DOCX files found."}
        
    libreoffice_bin = find_libreoffice()
    if not libreoffice_bin:
        return {"total": total, "success": 0, "failed": total, "error": "LibreOffice not found on system."}
        
    success_count = 0
    failed_count = 0
    
    for idx, docx in enumerate(docx_files, start=1):
        if progress_callback:
            progress_callback(idx, total, docx.name, "Converting...")
            
        cmd = [
            libreoffice_bin,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(docx)
        ]
        
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
            if res.returncode == 0:
                success_count += 1
                if progress_callback:
                    progress_callback(idx, total, docx.name, "Success")
            else:
                failed_count += 1
                if progress_callback:
                    progress_callback(idx, total, docx.name, f"Failed: {res.stderr}")
        except Exception as e:
            failed_count += 1
            if progress_callback:
                progress_callback(idx, total, docx.name, f"Error: {str(e)}")
                
    return {
        "total": total,
        "success": success_count,
        "failed": failed_count,
        "error": None
    }
