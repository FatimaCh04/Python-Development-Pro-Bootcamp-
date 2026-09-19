import streamlit as st
import pandas as pd
from pathlib import Path
import os
import time
import zipfile
import io

# ==========================================
# CORE BACKEND IMPORTS (100% Python Logic)
# ==========================================
from core.pdf_extractor import extract_pdf_data, ExtractionError
from core.data_cleaner import normalize_column_names, clean_data
from core.validator import validate_data
from core.mail_merger import generate_documents
from core.pdf_converter import convert_to_pdf_batch, find_libreoffice

# ==========================================
# CONFIGURATION & PATHS
# ==========================================
st.set_page_config(
    page_title="PDF Employee Mail Merge",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_WORD_DIR = BASE_DIR / "output" / "word"
OUTPUT_PDF_DIR = BASE_DIR / "output" / "pdf"

# Ensure directories exist
for d in [INPUT_DIR, DATA_DIR, TEMPLATE_DIR, OUTPUT_WORD_DIR, OUTPUT_PDF_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ==========================================
# CUSTOM CSS (Professional Enterprise Style)
# ==========================================
st.markdown("""
<style>
    /* Global Typography & Colors */
    body {
        color: #1e293b;
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Subtle Headers */
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* System Status */
    .system-status {
        font-size: 0.9rem;
        font-weight: 500;
        color: #10b981; /* Emerald */
        background-color: #ecfdf5;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 20px;
        border: 1px solid #a7f3d0;
    }
    
    /* Workflow Navigation */
    .workflow-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 30px;
        font-size: 0.9rem;
        font-weight: 500;
        color: #64748b;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .workflow-item { display: flex; align-items: center; }
    .workflow-active { color: #2563eb; font-weight: 700; }
    .workflow-completed { color: #10b981; }
    .workflow-arrow { margin: 0 10px; color: #cbd5e1; }
    
    /* Section Containers */
    .section-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1e293b;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Architecture Diagram */
    .arch-box {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 15px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #334155;
        line-height: 1.4;
    }
    
    /* File Status Text */
    .file-ready {
        color: #10b981;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Empty State Text */
    .empty-state {
        color: #64748b;
        font-style: italic;
        padding: 20px 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if 'stage' not in st.session_state:
    st.session_state.stage = 1  # 1:Upload, 2:Extract, 3:Validate, 4:Generate, 5:Convert, 6:Export
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'pdf_pages': 0,
        'records_extracted': 0,
        'valid_records': 0,
        'invalid_records': 0,
        'duplicates': 0,
        'docx_generated': 0,
        'pdf_generated': 0,
        'docx_failed': 0,
        'pdf_failed': 0,
        'start_time': 0.0,
        'processing_time': 0.0
    }
if 'raw_df' not in st.session_state:
    st.session_state.raw_df = pd.DataFrame()
if 'valid_df' not in st.session_state:
    st.session_state.valid_df = pd.DataFrame()
if 'invalid_df' not in st.session_state:
    st.session_state.invalid_df = pd.DataFrame()
if 'val_report' not in st.session_state:
    st.session_state.val_report = {}
if 'completed_steps' not in st.session_state:
    st.session_state.completed_steps = []

def mark_step(step_name):
    if step_name not in st.session_state.completed_steps:
        st.session_state.completed_steps.append(step_name)

def update_stage(new_stage):
    if new_stage > st.session_state.stage:
        st.session_state.stage = new_stage


# ==========================================
# HEADER & ARCHITECTURE
# ==========================================
st.markdown("<h1>PDF Employee Mail Merge Automation</h1>", unsafe_allow_html=True)
st.markdown("<h4>Automated PDF Data Extraction & Document Generation</h4>", unsafe_allow_html=True)
st.markdown("<div class='system-status'>● System Ready</div>", unsafe_allow_html=True)

with st.expander("View Processing Pipeline Architecture"):
    st.markdown("""
    <div class='arch-box'>
    PDF<br>
    &nbsp;↓<br>
    PDF Extraction (pdfplumber / Camelot)<br>
    &nbsp;↓<br>
    Pandas DataFrame<br>
    &nbsp;↓<br>
    Validation & Cleaning<br>
    &nbsp;↓<br>
    DOCX Mail Merge (docxtpl)<br>
    &nbsp;↓<br>
    DOCX Documents<br>
    &nbsp;↓<br>
    PDF Conversion (LibreOffice)<br>
    &nbsp;↓<br>
    Final Output
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# TOP STATISTICS
# ==========================================
s = st.session_state.stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("PDF Pages", s['pdf_pages'] if s['pdf_pages'] > 0 else "--")
with col2:
    st.metric("Records", s['records_extracted'] if s['records_extracted'] > 0 else "--")
with col3:
    st.metric("Valid", s['valid_records'] if s['valid_records'] > 0 else "--")
with col4:
    st.metric("Documents", s['docx_generated'] if s['docx_generated'] > 0 else "--")

st.markdown("<hr style='margin: 15px 0 25px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)


# ==========================================
# WORKFLOW NAVIGATION
# ==========================================
def get_nav_class(stage_num):
    if st.session_state.stage == stage_num:
        return "workflow-item workflow-active"
    elif st.session_state.stage > stage_num:
        return "workflow-item workflow-completed"
    return "workflow-item"

st.markdown(f"""
<div class='workflow-nav'>
    <div class='{get_nav_class(1)}'>01 Upload</div>
    <div class='workflow-arrow'>➔</div>
    <div class='{get_nav_class(2)}'>02 Extract</div>
    <div class='workflow-arrow'>➔</div>
    <div class='{get_nav_class(3)}'>03 Validate</div>
    <div class='workflow-arrow'>➔</div>
    <div class='{get_nav_class(4)}'>04 Generate</div>
    <div class='workflow-arrow'>➔</div>
    <div class='{get_nav_class(5)}'>05 Convert</div>
    <div class='workflow-arrow'>➔</div>
    <div class='{get_nav_class(6)}'>06 Export</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 01 — UPLOAD SOURCES
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>01 — Upload Sources</div>", unsafe_allow_html=True)

up_col1, up_col2 = st.columns(2)
with up_col1:
    st.markdown("**Employee Data PDF**")
    pdf_file = st.file_uploader("Accepts .pdf", type=['pdf'], label_visibility="collapsed")
    if pdf_file:
        with open(INPUT_DIR / "employees.pdf", "wb") as f:
            f.write(pdf_file.getbuffer())
        st.markdown(f"*{pdf_file.name}* ({pdf_file.size / 1024:.1f} KB)<br><span class='file-ready'>✓ Ready</span>", unsafe_allow_html=True)
        mark_step("PDF uploaded")
        
with up_col2:
    st.markdown("**Word Mail Merge Template**")
    tpl_file = st.file_uploader("Accepts .docx", type=['docx'], label_visibility="collapsed")
    if tpl_file:
        with open(TEMPLATE_DIR / "employee_template.docx", "wb") as f:
            f.write(tpl_file.getbuffer())
        st.markdown(f"*{tpl_file.name}* ({tpl_file.size / 1024:.1f} KB)<br><span class='file-ready'>✓ Ready</span>", unsafe_allow_html=True)
        mark_step("Word template uploaded")

if pdf_file and tpl_file:
    update_stage(2)

st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 02 — EXTRACT EMPLOYEE DATA
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>02 — Extract Employee Data</div>", unsafe_allow_html=True)
st.write("> Extract employee records from the uploaded PDF and convert them into structured tabular data.")

if st.session_state.stage < 2:
    st.markdown("<div class='empty-state'>Upload your employee PDF and Word template to begin extraction.</div>", unsafe_allow_html=True)
else:
    if st.button("Extract Employee Data", type="primary"):
        st.session_state.stats['start_time'] = time.time()
        with st.spinner("Executing PDF extraction backend (pdfplumber/Camelot)..."):
            try:
                df, summary = extract_pdf_data(INPUT_DIR / "employees.pdf")
                st.session_state.raw_df = df
                st.session_state.stats['pdf_pages'] = summary['total_pages']
                st.session_state.stats['records_extracted'] = summary['record_count']
                
                # Save raw outputs
                df.to_csv(DATA_DIR / "employees.csv", index=False)
                df.to_excel(DATA_DIR / "employees.xlsx", index=False)
                
                mark_step("Employee data extracted")
                update_stage(3)
                st.rerun()
            except ExtractionError as ee:
                st.error(f"Extraction could not be completed.\n\n{str(ee)}\n\nPlease verify that the PDF contains selectable text or tabular data.")
            except Exception as e:
                st.error(f"Unexpected extraction failure: {str(e)}")

    if not st.session_state.raw_df.empty:
        st.success(f"✓ Successfully extracted {st.session_state.stats['records_extracted']} records across {st.session_state.stats['pdf_pages']} pages.")
        with st.expander("View Extracted Data Preview"):
            st.dataframe(st.session_state.raw_df, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 03 — VALIDATE EMPLOYEE DATA
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>03 — Validate Employee Data</div>", unsafe_allow_html=True)

if st.session_state.stage < 3:
    st.markdown("<div class='empty-state'>Complete data extraction first.</div>", unsafe_allow_html=True)
else:
    if st.button("Validate Data", type="primary"):
        with st.spinner("Running validation backend..."):
            try:
                norm_df = normalize_column_names(st.session_state.raw_df)
                cleaned_df = clean_data(norm_df)
                valid_df, invalid_df, report = validate_data(cleaned_df)
                
                st.session_state.valid_df = valid_df
                st.session_state.invalid_df = invalid_df
                st.session_state.val_report = report
                
                st.session_state.stats['valid_records'] = report['valid_records']
                st.session_state.stats['invalid_records'] = report['invalid_records']
                st.session_state.stats['duplicates'] = report['duplicate_ids']
                
                valid_df.to_csv(DATA_DIR / "cleaned_employees.csv", index=False)
                valid_df.to_excel(DATA_DIR / "cleaned_employees.xlsx", index=False)
                
                mark_step("Data validation completed")
                update_stage(4)
                st.rerun()
            except Exception as e:
                st.error(f"Validation failure: {str(e)}")

    if st.session_state.val_report:
        rep = st.session_state.val_report
        vc1, vc2, vc3, vc4, vc5 = st.columns(5)
        vc1.metric("Total Records", rep['total_records'])
        vc2.metric("Valid Records", rep['valid_records'])
        vc3.metric("Invalid Records", rep['invalid_records'])
        vc4.metric("Duplicate IDs", rep['duplicate_ids'])
        vc5.metric("Missing Fields", sum(rep['missing_fields'].values()) if rep['missing_fields'] else 0)
        
        if rep['invalid_records'] > 0:
            with st.expander("View Validation Issues (Problematic Records)"):
                st.warning("The following records contain missing required fields or duplicates. They will be skipped.")
                st.dataframe(st.session_state.invalid_df, use_container_width=True)
                if rep['missing_fields']:
                    st.json(rep['missing_fields'])
                    
        st.markdown("### Employee Data Preview (Validated)")
        st.dataframe(st.session_state.valid_df, use_container_width=True)
        
        dl_col1, dl_col2, _ = st.columns([1, 1, 4])
        with open(DATA_DIR / "cleaned_employees.csv", "rb") as f:
            dl_col1.download_button("Download CSV", f, "cleaned_employees.csv", "text/csv")
        with open(DATA_DIR / "cleaned_employees.xlsx", "rb") as f:
            dl_col2.download_button("Download Excel", f, "cleaned_employees.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 04 — GENERATE EMPLOYEE DOCUMENTS
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>04 — Generate Employee Documents</div>", unsafe_allow_html=True)
st.write("> Generate a personalized Word document for every valid employee record using the uploaded template.")

if st.session_state.stage < 4:
    st.markdown("<div class='empty-state'>No validated records available. Complete data extraction and validation first.</div>", unsafe_allow_html=True)
else:
    if st.button("Generate Employee Documents", type="primary", disabled=st.session_state.valid_df.empty):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def merge_callback(idx, total, name, msg):
            progress_bar.progress(idx / total)
            status_text.text(f"Generating Documents...\n\n{idx} / {total} | {name}")
            
        try:
            res = generate_documents(
                st.session_state.valid_df,
                TEMPLATE_DIR / "employee_template.docx",
                OUTPUT_WORD_DIR,
                progress_callback=merge_callback
            )
            st.session_state.stats['docx_generated'] = res['success']
            st.session_state.stats['docx_failed'] = res['failed']
            
            mark_step("Word documents generated")
            update_stage(5)
            status_text.success(f"✓ {res['success']} DOCX documents generated successfully.")
            if res['failed'] > 0:
                st.warning(f"Failed to generate {res['failed']} documents. See console logs for details.")
                
            time.sleep(1) # Brief pause for UI update
            st.rerun()
        except Exception as e:
            st.error(f"Document generation failed: {str(e)}")

    if st.session_state.stats['docx_generated'] > 0:
        st.success(f"✓ {st.session_state.stats['docx_generated']} DOCX documents generated.")

st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 05 — CONVERT DOCUMENTS TO PDF
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>05 — Convert Documents to PDF</div>", unsafe_allow_html=True)
st.write("> Uses LibreOffice headless conversion to securely convert DOCX to PDF without data leaving the machine.")

if st.session_state.stage < 5:
    st.markdown("<div class='empty-state'>Generate DOCX documents first.</div>", unsafe_allow_html=True)
else:
    if st.button("Convert to PDF", type="primary", disabled=(st.session_state.stats['docx_generated'] == 0)):
        
        # Check LibreOffice first
        if not find_libreoffice():
            st.error("LibreOffice is not installed or not found in system PATH.")
            st.markdown("""
            **To enable automatic PDF conversion, install LibreOffice:**
            * **Windows (Command Line):** `winget install TheDocumentFoundation.LibreOffice`
            * **Windows (Manual):** Download from https://www.libreoffice.org
            * **Linux:** `sudo apt-get install libreoffice`
            * **macOS:** `brew install --cask libreoffice`
            
            *Note: Your DOCX files are safely generated in `output/word/`. Restart the app after installing LibreOffice.*
            """)
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def pdf_callback(idx, total, name, msg):
                progress_bar.progress(idx / total)
                status_text.text(f"Converting to PDF...\n\n{idx} / {total} | {name}")
                
            try:
                res = convert_to_pdf_batch(OUTPUT_WORD_DIR, OUTPUT_PDF_DIR, progress_callback=pdf_callback)
                if res.get('error'):
                    st.error(f"Conversion Error: {res['error']}")
                else:
                    st.session_state.stats['pdf_generated'] = res['success']
                    st.session_state.stats['pdf_failed'] = res['failed']
                    
                    st.session_state.stats['processing_time'] = time.time() - st.session_state.stats['start_time']
                    mark_step("PDF conversion completed")
                    mark_step("Output package ready")
                    update_stage(6)
                    status_text.success(f"✓ {res['success']} PDF documents converted successfully.")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"PDF conversion failed: {str(e)}")

    if st.session_state.stats['pdf_generated'] > 0 or st.session_state.stats['pdf_failed'] > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("DOCX Files", st.session_state.stats['docx_generated'])
        c2.metric("PDF Converted", st.session_state.stats['pdf_generated'])
        c3.metric("Failed", st.session_state.stats['pdf_failed'])

st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 06 — EXPORT & DOWNLOAD
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>06 — Export & Download</div>", unsafe_allow_html=True)

if st.session_state.stage < 6:
    st.markdown("<div class='empty-state'>Complete the PDF conversion step to generate the final output package.</div>", unsafe_allow_html=True)
else:
    st.write("Download your complete processed package containing Data, Word Documents, and PDFs.")
    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # Define internal structure: Employee_Mail_Merge_Output/
        root_zip_dir = "Employee_Mail_Merge_Output"
        
        # Add Data
        for f in DATA_DIR.glob("*.*"):
            if f.suffix in ['.xlsx', '.csv'] and 'cleaned' in f.name:
                z.write(f, f"{root_zip_dir}/data/{f.name}")
        
        # Add Word
        for f in OUTPUT_WORD_DIR.glob("*.docx"):
            z.write(f, f"{root_zip_dir}/word/{f.name}")
            
        # Add PDF
        for f in OUTPUT_PDF_DIR.glob("*.pdf"):
            z.write(f, f"{root_zip_dir}/pdf/{f.name}")
            
    st.download_button(
        label="Download All as ZIP", 
        data=buf.getvalue(), 
        file_name="Employee_Mail_Merge_Output.zip", 
        mime="application/zip",
        type="primary"
    )

st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# 07 — PROCESSING REPORT
# ==========================================
st.markdown("<div class='section-box'><div class='section-title'>07 — Processing Report</div>", unsafe_allow_html=True)

s = st.session_state.stats
report_md = f"""
### Processing Summary

| Metric | Value |
|--------|-------|
| PDF Pages | {s['pdf_pages']} |
| Records Extracted | {s['records_extracted']} |
| Valid Records | {s['valid_records']} |
| Invalid Records | {s['invalid_records']} |
| Duplicate Records | {s['duplicates']} |
| DOCX Generated | {s['docx_generated']} |
| PDF Generated | {s['pdf_generated']} |
| Failed Documents | {s['docx_failed'] + s['pdf_failed']} |
| Processing Time | {s['processing_time']:.2f} seconds |
"""

col_sum, col_log = st.columns([1, 1])
with col_sum:
    st.markdown(report_md)

with col_log:
    st.markdown("### Processing Log")
    if not st.session_state.completed_steps:
        st.markdown("<div class='empty-state'>No operations completed yet.</div>", unsafe_allow_html=True)
    else:
        for step in st.session_state.completed_steps:
            st.markdown(f"<span style='color: #10b981; font-weight: bold;'>✓</span> {step}", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
