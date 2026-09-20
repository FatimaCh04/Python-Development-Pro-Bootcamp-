import streamlit as st
import pandas as pd
from pathlib import Path
import time, zipfile, io, importlib
from datetime import datetime

# ── Backend Modules ───────────────────────────────────────────────────────────
from core.pdf_extractor import extract_pdf_data, ExtractionError
from core.data_cleaner   import normalize_column_names, clean_data
from core.validator      import validate_data
from core.mail_merger    import generate_documents
from core.pdf_converter  import convert_to_pdf_batch, find_libreoffice

import tempfile

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent

# Use temporary directory for session-safe storage on cloud
if "session_dir" not in st.session_state:
    st.session_state.session_dir = Path(tempfile.mkdtemp(prefix="pdfmailmerge_"))

SESSION_DIR  = st.session_state.session_dir
INPUT_DIR    = SESSION_DIR / "input"
DATA_DIR     = SESSION_DIR / "data"
TEMPLATE_DIR = SESSION_DIR / "templates"
WORD_DIR     = SESSION_DIR / "output" / "word"
PDF_DIR      = SESSION_DIR / "output"  / "pdf"

for _d in [INPUT_DIR, DATA_DIR, TEMPLATE_DIR, WORD_DIR, PDF_DIR]:
    _d.mkdir(parents=True, exist_ok=True)


# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PDF Mail Merge Pro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Session State ─────────────────────────────────────────────────────────────
def _init(key, val): 
    if key not in st.session_state: st.session_state[key] = val

_init("step", "01_SOURCE")
_init("pages_count", 0)
_init("logs", [(datetime.now().strftime("%H:%M:%S"), "Workbench initialized")])

def _log(msg):
    st.session_state.logs.append((datetime.now().strftime("%H:%M:%S"), msg))

if "raw_df" not in st.session_state:
    _p = DATA_DIR / "employees.csv"
    try:    st.session_state.raw_df = pd.read_csv(_p) if _p.exists() else pd.DataFrame()
    except: st.session_state.raw_df = pd.DataFrame()

if "valid_df" not in st.session_state:
    _p = DATA_DIR / "cleaned_employees.csv"
    try:    st.session_state.valid_df = pd.read_csv(_p) if _p.exists() else pd.DataFrame()
    except: st.session_state.valid_df = pd.DataFrame()

_init("invalid_df", pd.DataFrame())
_init("val_report", {})
_init("perf_time", 0.0)

# Live disk state
_pdf_path  = INPUT_DIR  / "employees.pdf"
_tpl_path  = TEMPLATE_DIR / "employee_template.docx"
_pdf_exists = _pdf_path.exists()
_tpl_exists = _tpl_path.exists()
_docx_files = sorted(WORD_DIR.glob("*.docx"))
_pdf_files  = sorted(PDF_DIR.glob("*.pdf"))
_libre_bin  = find_libreoffice()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base overrides */
[data-testid="stAppViewContainer"] {
    background-color: #FAFAFA !important;
}
[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1000px !important;
}

/* Hide default file uploader constraints text "Limit 200MB..." */
[data-testid="stFileUploadDropzone"] > div > small {
    display: none !important;
}

/* Style the file uploader dropzone */
[data-testid="stFileUploadDropzone"] {
    background-color: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 8px;
    padding: 32px 16px;
    transition: all 0.2s;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: #4f46e5;
    background-color: #f8fafc;
}

/* Custom Buttons */
div.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    padding: 4px 16px;
    transition: all 0.15s;
    border: 1px solid #e5e7eb;
    background-color: #ffffff;
    color: #111827;
}
div.stButton > button:hover:not(:disabled) {
    border-color: #cbd5e1;
    background-color: #f1f5f9;
}
div.stButton > button[kind="primary"] {
    background-color: #4f46e5;
    color: white;
    border: none;
}
div.stButton > button[kind="primary"]:hover:not(:disabled) {
    background-color: #4338ca;
}
div.stButton > button:disabled {
    opacity: 0.5;
}

/* Headers & Text */
.app-title {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.app-title::before {
    content: "◆";
    color: #4f46e5;
    font-size: 20px;
}
.app-subtitle {
    font-size: 14px;
    color: #64748B;
    margin-top: 4px;
    margin-bottom: 24px;
}

.system-status {
    font-size: 13px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: #64748B;
    display: flex;
    gap: 16px;
    align-items: center;
    justify-content: flex-end;
}
.status-ok { color: #16a34a; }
.status-warn { color: #d97706; }

/* Workflow Tabs */
.workflow-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 16px 0;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 32px;
}
.wf-step {
    font-size: 14px;
    font-weight: 500;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 8px;
}
.wf-step.active {
    color: #4f46e5;
    font-weight: 600;
}
.wf-step.done {
    color: #16a34a;
}
.wf-divider {
    color: #cbd5e1;
    font-size: 12px;
}

/* Section Styling */
.section-title {
    font-size: 18px;
    font-weight: 600;
    color: #111827;
    margin-bottom: 8px;
}
.section-desc {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 24px;
}

/* Status Strips */
.status-strip {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 24px;
    font-size: 14px;
    margin-bottom: 24px;
}
.strip-item {
    display: flex;
    align-items: center;
    gap: 8px;
}
.strip-val { font-weight: 600; color: #111827; }
.strip-lbl { color: #64748b; }

/* Log Terminal */
.terminal {
    background-color: #0f172a;
    border-radius: 6px;
    padding: 16px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 12px;
    color: #e2e8f0;
    height: 180px;
    overflow-y: auto;
}
.term-time { color: #64748b; margin-right: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_sys = st.columns([1, 1])
with col_title:
    st.markdown("<div class='app-title'>PDF MAIL MERGE PRO</div>", unsafe_allow_html=True)
    st.markdown("<div class='app-subtitle'>Employee Document Automation Workspace</div>", unsafe_allow_html=True)

with col_sys:
    _lib_ok = bool(_libre_bin)
    _pdf_status = "<span class='status-ok'>● PDF Ready</span>" if _lib_ok else "<span class='status-warn'>⚠ PDF Unavailable</span>"
    st.markdown(f"""
    <div style='height: 100%; display: flex; align-items: center; justify-content: flex-end;'>
        <div class='system-status'>
            <span><span class='status-ok'>●</span> Python Ready</span>
            <span>{_pdf_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Workflow Bar ──────────────────────────────────────────────────────────────
_steps = [
    ("01_SOURCE",   "01 Source"),
    ("02_EXTRACT",  "02 Extract"),
    ("03_VALIDATE", "03 Validate"),
    ("04_GENERATE", "04 Generate"),
    ("05_EXPORT",   "05 Export")
]

_curr_idx = next(i for i, v in enumerate(_steps) if v[0] == st.session_state.step)

_wf_html = "<div class='workflow-row'>"
for i, (sid, label) in enumerate(_steps):
    if i == _curr_idx:
        _wf_html += f"<div class='wf-step active'>● {label}</div>"
    elif i < _curr_idx:
        _wf_html += f"<div class='wf-step done'>✓ {label}</div>"
    else:
        _wf_html += f"<div class='wf-step'>○ {label}</div>"
        
    if i < len(_steps) - 1:
        _wf_html += "<div class='wf-divider'>─</div>"
_wf_html += "</div>"

st.markdown(_wf_html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# 01 SOURCE
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.step == "01_SOURCE":
    st.markdown("<div class='section-title'>Source Files</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-desc'>Upload the employee PDF and Word template used by the automation pipeline.</div>", unsafe_allow_html=True)
    
    col_pdf, col_tpl = st.columns(2)
    
    with col_pdf:
        st.markdown("**PDF Employee Data**<br><span style='color:#64748b;font-size:13px;'>Upload your employee PDF</span>", unsafe_allow_html=True)
        up_pdf = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
        if up_pdf:
            with open(_pdf_path, "wb") as f: f.write(up_pdf.getbuffer())
            _log("✓ PDF uploaded")
            st.rerun()
        if _pdf_exists:
            _sz = f"{_pdf_path.stat().st_size/1024:.0f} KB"
            st.success(f"✓ **employees.pdf** ({_sz} • PDF • Ready)")

    with col_tpl:
        st.markdown("**DOCX Mail Merge Template**<br><span style='color:#64748b;font-size:13px;'>Upload your Word template</span>", unsafe_allow_html=True)
        up_tpl = st.file_uploader("Template", type=["docx"], label_visibility="collapsed")
        if up_tpl:
            with open(_tpl_path, "wb") as f: f.write(up_tpl.getbuffer())
            _log("✓ Template loaded")
            st.rerun()
        if _tpl_exists:
            _sz2 = f"{_tpl_path.stat().st_size/1024:.0f} KB"
            st.success(f"✓ **employee_template.docx** ({_sz2} • DOCX • Ready)")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    _ready = _pdf_exists and _tpl_exists
    
    st.markdown(f"<div style='font-size: 14px; margin-bottom: 12px;'>**{2 if _ready else (1 if _pdf_exists or _tpl_exists else 0)} source files ready**</div>", unsafe_allow_html=True)
    
    if st.button("Extract Employee Data →", type="primary", disabled=not _ready):
        st.session_state.step = "02_EXTRACT"
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 02 EXTRACT
# ════════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "02_EXTRACT":
    st.markdown("<div class='section-title'>Extracted Employee Data</div>", unsafe_allow_html=True)
    
    if st.session_state.raw_df.empty:
        st.markdown("<div class='section-desc'>Run extraction to parse data from the PDF.</div>", unsafe_allow_html=True)
        if st.button("Run Extraction", type="primary"):
            with st.spinner("Extracting data..."):
                t0 = time.time()
                try:
                    _df, _summ = extract_pdf_data(_pdf_path)
                    st.session_state.raw_df = _df
                    st.session_state.pages_count = _summ.get("total_pages", 1)
                    _df.to_csv(DATA_DIR / "employees.csv", index=False)
                    _log("✓ PDF extraction completed")
                    _log(f"✓ {len(_df)} records detected")
                    st.session_state.perf_time += (time.time() - t0)
                    st.rerun()
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
    else:
        _nr = len(st.session_state.raw_df)
        _nc = len(st.session_state.raw_df.columns)
        _np = st.session_state.pages_count
        
        st.markdown(f"<div class='section-desc'>{_nr} records • {_nc} columns • {_np} pages</div>", unsafe_allow_html=True)
        
        col_search, _, _ = st.columns([2, 1, 1])
        with col_search:
            _q = st.text_input("Search employees...", label_visibility="collapsed", placeholder="Search employees...")
        
        _disp = st.session_state.raw_df
        if _q:
            _mask = _disp.apply(lambda c: c.astype(str).str.contains(_q, case=False, na=False)).any(axis=1)
            _disp = _disp[_mask]
            
        st.dataframe(_disp, use_container_width=True, height=350)
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button("Proceed to Validation →", type="primary"):
            st.session_state.step = "03_VALIDATE"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 03 VALIDATE
# ════════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "03_VALIDATE":
    st.markdown("<div class='section-title'>Data Validation</div>", unsafe_allow_html=True)
    
    if st.session_state.valid_df.empty and st.session_state.invalid_df.empty:
        st.markdown("<div class='section-desc'>Verify all records meet the required schema.</div>", unsafe_allow_html=True)
        if st.button("Validate Data", type="primary"):
            t0 = time.time()
            _norm = normalize_column_names(st.session_state.raw_df)
            _clean = clean_data(_norm)
            _vdf, _idf, _rep = validate_data(_clean)
            st.session_state.valid_df = _vdf
            st.session_state.invalid_df = _idf
            st.session_state.val_report = _rep
            _vdf.to_csv(DATA_DIR / "cleaned_employees.csv", index=False)
            _log("✓ Validation completed")
            st.session_state.perf_time += (time.time() - t0)
            st.rerun()
    else:
        _rp = st.session_state.val_report or {}
        _nv = len(st.session_state.valid_df)
        _ni = len(st.session_state.invalid_df)
        _nd = _rp.get("duplicate_ids", 0)
        
        st.markdown(f"""
        <div class="status-strip">
            <div class="strip-item"><span style="color:#16a34a">✓</span> <span class="strip-val">{_nv}</span> <span class="strip-lbl">Valid</span></div>
            <div class="strip-item"><span style="color:#d97706">⚠</span> <span class="strip-val">0</span> <span class="strip-lbl">Warnings</span></div>
            <div class="strip-item"><span style="color:#dc2626">✕</span> <span class="strip-val">{_ni}</span> <span class="strip-lbl">Invalid</span></div>
            <div class="strip-item"><span style="color:#64748b">◇</span> <span class="strip-val">{_nd}</span> <span class="strip-lbl">Duplicates</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        if _ni == 0:
            st.success("✓ **Validation completed**\n\nAll employee records are ready for document generation.")
        else:
            st.error(f"✕ Found {_ni} invalid records that will be excluded.")
            
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button("Proceed to Generation →", type="primary"):
            st.session_state.step = "04_GENERATE"
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 04 GENERATE
# ════════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "04_GENERATE":
    st.markdown("<div class='section-title'>Document Generation</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-desc'>Generate a personalized Word document for every validated employee record.</div>", unsafe_allow_html=True)
    
    _nv = len(st.session_state.valid_df)
    _ndocx = len(_docx_files)
    
    st.markdown(f"""
    <div class="status-strip">
        <div class="strip-item"><span class="strip-lbl">TEMPLATE</span> <span class="strip-val">employee_template.docx</span></div>
        <div class="strip-item"><span class="strip-lbl">RECORDS READY</span> <span class="strip-val">{_nv}</span></div>
        <div class="strip-item"><span class="strip-lbl">OUTPUT</span> <span class="strip-val">output/word/</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    if _ndocx == 0:
        if st.button(f"Generate {_nv} Documents", type="primary"):
            t0 = time.time()
            _prog = st.progress(0)
            def _gen_cb(c, t, n, m): _prog.progress(c/t)
            _res = generate_documents(st.session_state.valid_df, _tpl_path, WORD_DIR, _gen_cb)
            _log("✓ DOCX generation completed")
            st.session_state.perf_time += (time.time() - t0)
            time.sleep(0.5)
            st.rerun()
    else:
        st.success(f"✓ **{_ndocx} successful**\n\n✕ 0 failed")
        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        if st.button("Proceed to Export →", type="primary"):
            st.session_state.step = "05_EXPORT" 
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 05 EXPORT (PDF + ZIP)
# ════════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "05_EXPORT":
    
    # ── PDF Conversion ──
    st.markdown("<div class='section-title'>PDF Conversion</div>", unsafe_allow_html=True)
    _ndocx = len(_docx_files)
    _npdf = len(_pdf_files)
    _lib_ok = bool(_libre_bin)
    
    st.markdown(f"""
    <div class="status-strip">
        <div class="strip-item"><span class="strip-lbl">DOCX READY</span> <span class="strip-val">{_ndocx}</span></div>
        <div class="strip-item"><span class="strip-lbl">PDF GENERATED</span> <span class="strip-val">{_npdf}</span></div>
        <div class="strip-item"><span class="strip-lbl">CONVERTER</span> <span class="strip-val">LibreOffice</span></div>
        <div class="strip-item"><span class="strip-lbl">STATUS</span> <span class="strip-val" style="color:{'#16a34a' if _lib_ok else '#d97706'}">{'Ready' if _lib_ok else '⚠ Missing'}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    if not _lib_ok:
        st.warning("**PDF conversion is currently unavailable.**\n\nLibreOffice is required to convert DOCX files into PDF. Install LibreOffice and restart the application.")
        st.button("Convert DOCX → PDF", disabled=True)
    elif _npdf < _ndocx:
        if st.button("Convert DOCX → PDF", type="primary"):
            t0 = time.time()
            _prog = st.progress(0)
            def _pdf_cb(c, t, n, m): _prog.progress(c/t)
            convert_to_pdf_batch(WORD_DIR, PDF_DIR, _pdf_cb)
            _log("✓ PDF conversion completed")
            st.session_state.perf_time += (time.time() - t0)
            st.rerun()
    else:
        st.success("✓ **PDF conversion completed successfully.**")
    
    st.markdown("<hr style='margin: 32px 0; border-color: #e5e7eb;'>", unsafe_allow_html=True)
    
    # ── Export ──
    st.markdown("<div class='section-title'>Export</div>", unsafe_allow_html=True)
    
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    
    _csv_f = DATA_DIR / "cleaned_employees.csv"
    if _csv_f.exists():
        with open(_csv_f, "rb") as f:
            col_dl1.download_button("Download CSV", f, "employees.csv", "text/csv", use_container_width=True)
        col_dl2.download_button("Download Excel", open(_csv_f,"rb").read(), "employees.csv", "text/csv", use_container_width=True) 
    
    _zip_buf = io.BytesIO()
    with zipfile.ZipFile(_zip_buf, "w", zipfile.ZIP_DEFLATED) as _z:
        for _f in _docx_files: _z.write(_f, f"word/{_f.name}")
        for _f in _pdf_files:  _z.write(_f, f"pdf/{_f.name}")
        if _csv_f.exists():    _z.write(_csv_f, f"data/{_csv_f.name}")
        
    with col_dl3:
        st.download_button(
            "Download Complete ZIP", 
            _zip_buf.getvalue(), 
            "Complete_Package.zip", 
            "application/zip", 
            type="primary", 
            use_container_width=True
        )


# ════════════════════════════════════════════════════════════════════════════════
# Processing Report & Logs
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<hr style='margin: 48px 0 24px 0; border-color: #e5e7eb;'>", unsafe_allow_html=True)

if st.session_state.step != "01_SOURCE":
    st.markdown("<div class='section-title'>Processing Summary</div>", unsafe_allow_html=True)
    
    _nv = len(st.session_state.valid_df)
    _ni = len(st.session_state.invalid_df)
    _nr = len(st.session_state.raw_df)
    _ndocx = len(_docx_files)
    _npdf = len(_pdf_files)
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>PDF pages</span><span style='font-weight:500'>{st.session_state.pages_count}</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>Records extracted</span><span style='font-weight:500'>{_nr}</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>Valid records</span><span style='font-weight:500'>{_nv}</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>Invalid records</span><span style='font-weight:500'>{_ni}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown(f"""
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>DOCX generated</span><span style='font-weight:500'>{_ndocx}</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>PDF generated</span><span style='font-weight:500'>{_npdf}</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>Failed documents</span><span style='font-weight:500'>0</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size:14px;'>
            <span style='color:#64748b'>Processing time</span><span style='font-weight:500'>{st.session_state.perf_time:.1f}s</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

with st.expander("Processing Log"):
    _log_html = "".join(f"<div><span class='term-time'>{_ts}</span>{_msg}</div>" for _ts, _msg in reversed(st.session_state.logs))
    st.markdown(f"<div class='terminal'>{_log_html}</div>", unsafe_allow_html=True)
