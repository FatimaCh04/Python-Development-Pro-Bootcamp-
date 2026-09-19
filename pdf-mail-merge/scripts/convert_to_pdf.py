"""
Convert to PDF Module
Stage 4 of the PDF Employee Data to Mail Merge Pipeline.

Batch converts generated Word (.docx) documents to PDF using LibreOffice headless CLI.

Requirements handled:
- Detect LibreOffice installation.
- Headless command-line conversion.
- Individual PDF conversion for each DOCX.
- Preserve document formatting (LibreOffice native).
- Do not delete original DOCX files.
- Handle failures gracefully (no crash).
- Print per-file progress (Converting 1/200...)
- Print summary table at completion.
- Provide clear Windows installation instructions if LibreOffice is missing.
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Optional


def find_libreoffice() -> Optional[str]:
    """
    Detects LibreOffice executable across PATH and standard Windows OS installation directories.
    Returns the path to the executable if found, else None.
    """
    # 1. Check PATH
    for cmd in ["soffice", "libreoffice"]:
        found = shutil.which(cmd)
        if found:
            return found

    # 2. Check Windows standard paths
    if sys.platform.startswith("win"):
        candidate_paths = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "LibreOffice" / "program" / "soffice.exe",
            Path(r"D:\Program Files\LibreOffice\program\soffice.exe"),
        ]
        for p in candidate_paths:
            if p.is_file():
                return str(p)

    return None


def convert_file_with_libreoffice(libreoffice_cmd: str, docx_path: Path, output_dir: Path) -> bool:
    """
    Converts a single docx file to pdf via LibreOffice headless CLI.
    LibreOffice will place the PDF in the specified outdir without deleting the original.
    """
    try:
        cmd = [
            libreoffice_cmd,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(output_dir),
            str(docx_path)
        ]
        # Run conversion synchronously, capture output to avoid cluttering terminal
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60  # generous timeout for one file
        )
        if result.returncode == 0:
            return True
        else:
            # We can log the stderr if it failed
            print(f"\n[!] LibreOffice failed for {docx_path.name}: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"\n[!] Error converting {docx_path.name}: {e}")
        return False


def convert_word_to_pdf(
    input_path: Path,
    output_dir: Path,
    limit: Optional[int] = None
) -> int:
    """
    Main conversion routine.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gather DOCX files
    if input_path.is_file() and input_path.suffix.lower() == ".docx":
        docx_files = [input_path]
    elif input_path.is_dir():
        docx_files = sorted(list(input_path.glob("*.docx")))
    else:
        raise FileNotFoundError(f"Input path does not exist or is not a docx/directory: {input_path}")

    if not docx_files:
        print(f"[!] No .docx files found to convert in: {input_path}")
        return 0

    if limit and limit > 0:
        print(f"[*] --limit flag set: processing first {limit} records.")
        docx_files = docx_files[:limit]

    total = len(docx_files)
    
    # Check for LibreOffice
    libreoffice_bin = find_libreoffice()

    if not libreoffice_bin:
        print("\n" + "!" * 68)
        print("LIBREOFFICE NOT DETECTED")
        print("!" * 68)
        print("To enable automatic DOCX to PDF conversion, LibreOffice must be installed.")
        print("\nWindows Installation Instructions:")
        print("  Option 1 (Command Line): Open terminal and run:")
        print("                           winget install TheDocumentFoundation.LibreOffice")
        print("  Option 2 (Manual):       Download from https://www.libreoffice.org/download/")
        print("\nOnce installed, rerun this stage.")
        print("Your Word documents are safely preserved in: output/word/")
        print("!" * 68 + "\n")
        # Exit gracefully
        return 0

    print(f"[*] Detected LibreOffice at: {libreoffice_bin}")
    print("-" * 68)

    count_success = 0
    count_failed = 0

    for idx, docx_file in enumerate(docx_files, start=1):
        # Print progress formatted exactly as requested
        print(f"Converting {idx}/{total}")
        
        success = convert_file_with_libreoffice(libreoffice_bin, docx_file, output_dir)
        if success:
            count_success += 1
        else:
            count_failed += 1

    # Final Summary Table
    print("\n" + "=" * 68)
    print("  DOCX TO PDF CONVERSION COMPLETE")
    print("=" * 68)
    print(f"  Total DOCX files          : {total}")
    print(f"  Successful PDF conversions: {count_success}")
    print(f"  Failed conversions        : {count_failed}")
    print(f"  PDF output directory      : {output_dir.resolve()}")
    print("=" * 68 + "\n")

    return count_success


def main():
    parser = argparse.ArgumentParser(
        description="Convert generated Word documents to PDF using LibreOffice headless CLI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    _base = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=_base / "output" / "word",
        help="Input .docx file or directory of Word files"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=_base / "output" / "pdf",
        help="Directory to save converted PDF files"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of documents to convert"
    )
    args = parser.parse_args()

    print("\n" + "=" * 68)
    print("  STAGE 4: AUTOMATED PDF CONVERSION")
    print("=" * 68 + "\n")

    try:
        convert_word_to_pdf(args.input, args.output_dir, args.limit)
    except Exception as e:
        print(f"\n[ERROR] PDF conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
