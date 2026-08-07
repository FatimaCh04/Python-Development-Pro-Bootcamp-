"""
Sales Data Analyzer Pro — Enterprise Dashboard
Premium Glassmorphism UI (Power BI / Tableau / Salesforce style)
"""
import sys
import time
import io
import base64
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    CLEANED_DATA_FILE, SUMMARY_DATA_FILE, DATA_DIR,
    CHARTS_DIR, REPORTS_DIR, MODEL_FILE
)
from src.prediction import SalesPredictor
from src.cleaning import DataCleaner
from src.utils import generate_sample_data

# ───────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ───────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Data Analyzer Pro",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ───────────────────────────────────────────────────────────────────────────
# PREMIUM ENTERPRISE CSS (Glassmorphism & Animations)
# ───────────────────────────────────────────────────────────────────────────
ENTERPRISE_CSS = """
<style>
/* ── Fonts & Base Theme ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-main: #0B0F19;
    --glass-bg: rgba(23, 31, 50, 0.65);
    --glass-border: rgba(255, 255, 255, 0.08);
    --accent: #3B82F6;
    --accent-hover: #2563EB;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --text-primary: #F3F4F6;
    --text-muted: #9CA3AF;
}

.stApp {
    background-color: var(--bg-main);
    background-image: 
        radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.08), transparent 25%),
        radial-gradient(circle at 85% 30%, rgba(16, 185, 129, 0.05), transparent 25%);
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

/* ── Typography & Spacing ── */
.block-container { padding: 2.5rem 3rem 4rem 3rem !important; }
h1, h2, h3 { font-weight: 700 !important; letter-spacing: -0.02em !important; }

/* ── Glassmorphism Containers ── */
.glass-container {
    background: var(--glass-bg);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    margin-bottom: 1.5rem;
}
.glass-container:hover {
    box-shadow: 0 10px 32px -4px rgba(0, 0, 0, 0.4);
}

/* ── KPI Cards (Specific Glass layout) ── */
.kpi-card {
    background: linear-gradient(145deg, rgba(31, 41, 55, 0.7) 0%, rgba(17, 24, 39, 0.8) 100%);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.2rem;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    position: relative;
    overflow: hidden;
    height: 100%;
}
.kpi-card::after {
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px;
}
.kpi-card.blue::after { background: var(--accent); }
.kpi-card.green::after { background: var(--success); }
.kpi-card.gold::after { background: var(--warning); }
.kpi-card.purple::after { background: #8B5CF6; }

.kpi-top { display: flex; justify-content: space-between; align-items: flex-start; }
.kpi-icon { font-size: 1.5rem; opacity: 0.8; }
.kpi-title { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.kpi-value { font-size: 2rem; font-weight: 700; color: white; margin-bottom: 0.2rem; line-height: 1.1; }
.kpi-growth { font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 4px; }
.growth-pos { color: var(--success); }
.growth-neg { color: var(--danger); }

/* ── Sidebar Styling ── */
[data-testid="stSidebar"] {
    background-color: rgba(11, 15, 25, 0.95) !important;
    border-right: 1px solid var(--glass-border);
    min-width: 320px !important;
    max-width: 380px !important;
}
.sidebar-profile {
    display: flex; align-items: center; gap: 12px; padding: 1rem 0;
    border-bottom: 1px solid var(--glass-border); margin-bottom: 1.5rem;
}
.avatar { width: 44px; height: 44px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 1.2rem; }
.profile-info .name { font-weight: 600; font-size: 1.05rem; }
.profile-info .role { font-size: 0.85rem; color: var(--text-muted); }

/* ── Sidebar Navigation Menu (styled from st.radio) ── */
/* Remove default radio circle */
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
/* Style the item container */
[data-testid="stSidebar"] div[role="radiogroup"] > label {
    padding: 12px 16px !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
    background-color: transparent;
    border: 1px solid transparent;
    transition: all 0.2s ease-in-out;
    cursor: pointer;
    width: 100%;
}
/* Text alignment & sizing */
[data-testid="stSidebar"] div[role="radiogroup"] > label p {
    font-size: 17px !important;
    font-weight: 500 !important;
    color: #9CA3AF !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
}
/* Hover state */
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover p {
    color: #F3F4F6 !important;
}
/* Active selected state */
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background-color: var(--accent) !important;
    border: 1px solid var(--accent-hover) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
    color: white !important;
    font-weight: 600 !important;
}

/* ── Streamlit Overrides ── */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
}
.stButton > button {
    background: var(--accent) !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important; font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important; }

/* ── Table Styling ── */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid var(--glass-border); }

/* ── Plotly Containers ── */
.js-plotly-plot { border-radius: 12px !important; }

/* Subtle fade-in animation for main content */
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.block-container { animation: fadeIn 0.5s ease-out; }
</style>
"""
st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────
# PLOTLY PREMIUM TEMPLATE
# ───────────────────────────────────────────────────────────────────────────
ENTERPRISE_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F3F4F6", size=12),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False),
        margin=dict(l=40, r=20, t=40, b=40),
        hovermode="x unified",
        colorway=["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"]
    )
)
import plotly.io as pio
pio.templates.default = ENTERPRISE_TEMPLATE

# ───────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ───────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_main_data() -> pd.DataFrame | None:
    try:
        df = pd.read_csv(CLEANED_DATA_FILE)
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df = df.dropna(subset=["Date"])
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return None

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if not filters: return df
    if filters.get("date_range") and len(filters["date_range"]) == 2:
        df = df[(df["Date"].dt.date >= filters["date_range"][0]) & (df["Date"].dt.date <= filters["date_range"][1])]
    if filters.get("regions"):   df = df[df["Region"].isin(filters["regions"])]
    if filters.get("categories"):df = df[df["Category"].isin(filters["categories"])]
    if filters.get("products"):  df = df[df["Product"].isin(filters["products"])]
    if filters.get("payments"):  df = df[df["Payment_Method"].isin(filters["payments"])]
    return df

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()

# ───────────────────────────────────────────────────────────────────────────
# UI COMPONENTS
# ───────────────────────────────────────────────────────────────────────────
def render_sparkline(data: pd.Series, color: str) -> str:
    """Generates a base64 SVG sparkline for KPI cards."""
    if len(data) < 2: return ""
    
    # Normalize data for SVG viewBox (0-100 height)
    min_v, max_v = data.min(), data.max()
    if max_v == min_v: max_v = min_v + 1
    
    width = 120
    height = 30
    points = []
    for i, val in enumerate(data):
        x = (i / (len(data) - 1)) * width
        y = height - ((val - min_v) / (max_v - min_v) * height)
        points.append(f"{x},{y}")
        
    path_d = f"M {points[0]} " + " L ".join(points[1:])
    svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <path d="{path_d}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" style="opacity:0.8; margin-top:8px;">'

def render_kpi(title: str, value: str, icon: str, growth: float, sparkline_data: pd.Series, color_theme: str):
    is_pos = growth >= 0
    g_cls = "growth-pos" if is_pos else "growth-neg"
    g_icon = "↗" if is_pos else "↘"
    g_color = "#10B981" if is_pos else "#EF4444"
    
    spark = render_sparkline(sparkline_data, g_color)
    
    html = f"""
    <div class="kpi-card {color_theme}">
        <div class="kpi-top">
            <div>
                <div class="kpi-title">{title}</div>
                <div class="kpi-value">{value}</div>
            </div>
            <div class="kpi-icon">{icon}</div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:flex-end;">
            <div class="kpi-growth {g_cls}">{g_icon} {abs(growth):.1f}%</div>
            <div>{spark}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Header / Profile
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:1rem;">
        <div style="background:#3B82F6; padding:8px; border-radius:8px; font-size:1.2rem;">💠</div>
        <div style="font-weight:700; font-size:1.1rem; letter-spacing:0.5px;">Analytics Pro</div>
    </div>
    <div class="sidebar-profile">
        <div class="avatar">JD</div>
        <div class="profile-info">
            <div class="name">Jane Doe</div>
            <div class="role">VP of Sales</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    PAGES = [
        "🏠 Dashboard", 
        "🧹 Data Cleaning", 
        "📊 Sales Analysis", 
        "📈 Visualizations", 
        "🏆 Top Products", 
        "🤖 Prediction", 
        "📄 Reports", 
        "⚙️ Settings"
    ]
    selected_page = st.radio("NAVIGATION", PAGES, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filters
    st.markdown('<div style="font-size:0.8rem; font-weight:600; color:#9CA3AF; margin-bottom:0.5rem; text-transform:uppercase;">Global Filters</div>', unsafe_allow_html=True)
    
    df_raw = load_main_data()
    filters = {}
    
    if df_raw is not None and not df_raw.empty:
        with st.expander("📅 Date Range", expanded=True):
            min_d, max_d = df_raw["Date"].min().date(), df_raw["Date"].max().date()
            if "date_filter" not in st.session_state:
                st.session_state.date_filter = (min_d, max_d)
            date_range = st.date_input("Select Dates", value=st.session_state.date_filter, min_value=min_d, max_value=max_d, label_visibility="collapsed")
            if isinstance(date_range, tuple) and len(date_range) == 2:
                filters["date_range"] = date_range

        with st.expander("🌍 Regions & Categories"):
            filters["regions"] = st.multiselect("Regions", sorted(df_raw["Region"].unique()))
            filters["categories"] = st.multiselect("Categories", sorted(df_raw["Category"].unique()))
            
        with st.expander("🏷️ Products & Payments"):
            filters["products"] = st.multiselect("Products", sorted(df_raw["Product"].unique()))
            filters["payments"] = st.multiselect("Payment Method", sorted(df_raw["Payment_Method"].unique()))
            
        c1, c2 = st.columns(2)
        if c1.button("Apply Filters"): pass
        if c2.button("Reset Filters"):
            st.session_state.clear()
            st.rerun()

# ───────────────────────────────────────────────────────────────────────────
# MAIN LOGIC & FILTERING
# ───────────────────────────────────────────────────────────────────────────
if df_raw is None or df_raw.empty:
    st.error("Dataset could not be loaded. Please ensure data/cleaned_sales_data.csv exists.")
    st.stop()

df = apply_filters(df_raw, filters)

if len(df) == 0 and selected_page not in ["🧹 Data Cleaning", "⚙️ Settings", "📄 Reports"]:
    st.warning("⚠️ No data available for the selected filters. Please adjust your criteria.")
    st.stop()

# ───────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD (Home)
# ───────────────────────────────────────────────────────────────────────────
if selected_page == "🏠 Dashboard":
    st.markdown("<h1>Executive Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:var(--text-muted)'>Overview of performance from {df['Date'].min().date()} to {df['Date'].max().date()} | {len(df):,} records</p>", unsafe_allow_html=True)
    
    # ── KPIs ──
    last_date = df["Date"].max()
    curr_period = df[df["Date"] >= (last_date - pd.Timedelta(days=30))]
    prev_period = df[(df["Date"] < (last_date - pd.Timedelta(days=30))) & (df["Date"] >= (last_date - pd.Timedelta(days=60)))]
    
    def calc_growth(curr, prev):
        if prev == 0: return 0
        return ((curr - prev) / prev) * 100
        
    rev_c, rev_p = curr_period["Sales"].sum(), prev_period["Sales"].sum()
    prof_c, prof_p = curr_period["Profit"].sum(), prev_period["Profit"].sum()
    ord_c, ord_p = len(curr_period), len(prev_period)
    
    monthly_trend = df.set_index("Date")["Sales"].resample("ME").sum().tail(6)
    monthly_prof = df.set_index("Date")["Profit"].resample("ME").sum().tail(6)
    monthly_ord = df.set_index("Date")["Invoice_ID"].resample("ME").count().tail(6)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi("Total Revenue", f"${df['Sales'].sum()/1e6:.2f}M", "💰", calc_growth(rev_c, rev_p), monthly_trend, "blue")
    with c2: render_kpi("Total Profit", f"${df['Profit'].sum()/1e6:.2f}M", "📈", calc_growth(prof_c, prof_p), monthly_prof, "green")
    with c3: render_kpi("Total Orders", f"{len(df):,}", "🛒", calc_growth(ord_c, ord_p), monthly_ord, "gold")
    with c4: render_kpi("Avg Margin", f"{(df['Profit'].sum()/df['Sales'].sum()*100):.1f}%", "🎯", 0.5, monthly_prof, "purple")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Executive Summary Charts ──
    col_chart1, col_chart2 = st.columns([7, 3])
    
    with col_chart1:
    
        st.markdown("<h3>Revenue Trend</h3>", unsafe_allow_html=True)
        trend_df = df.set_index("Date")["Sales"].resample("ME").sum().reset_index()
        fig = px.area(trend_df, x="Date", y="Sales", color_discrete_sequence=["#3B82F6"])
        fig.update_traces(fillcolor="rgba(59, 130, 246, 0.2)", line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
    
        
    with col_chart2:
    
        st.markdown("<h3>Revenue by Region</h3>", unsafe_allow_html=True)
        reg_df = df.groupby("Region")["Sales"].sum().reset_index()
        fig = px.pie(reg_df, values="Sales", names="Region", hole=0.7)
        fig.update_traces(textinfo="none", hovertemplate="<b>%{label}</b><br>$%{value:,.0f}")
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2, x=0))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
        
    # ── Recent Transactions ──

    st.markdown("<h3>Recent Transactions</h3>", unsafe_allow_html=True)
    recent = df.sort_values("Date", ascending=False).head(50)[["Date", "Invoice_ID", "Customer", "Product", "Sales", "Profit"]]
    
    st.dataframe(
        recent,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="MMM DD, YYYY"),
            "Sales": st.column_config.NumberColumn("Revenue", format="$%f"),
            "Profit": st.column_config.NumberColumn("Profit", format="$%f"),
        },
        use_container_width=True,
        hide_index=True
    )


# ───────────────────────────────────────────────────────────────────────────
# PAGE: DATA CLEANING
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "🧹 Data Cleaning":
    st.markdown("<h1>Data Cleaning & Health</h1>", unsafe_allow_html=True)
    
    cleaner = DataCleaner()
    cleaner.load_data()
    cleaned = cleaner.clean_data()
    summary_c = cleaner.summary


    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Original Rows", f"{summary_c['Original Rows']:,}")
    c2.metric("Rows Removed", f"{summary_c['Rows Removed']:,}")
    c3.metric("Duplicates Removed", f"{summary_c['Duplicates Removed']:,}")
    c4.metric("Final Clean Rows", f"{summary_c['Final Rows']:,}")

    

    st.markdown("<h3>Data Preview (Cleaned)</h3>", unsafe_allow_html=True)
    st.dataframe(cleaned.head(100), use_container_width=True)
    
    c1, c2, _ = st.columns([1, 1, 3])
    with c1:
        st.download_button("Download Cleaned CSV", data=to_csv_bytes(cleaned), file_name="cleaned_sales.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.download_button("Download Excel", data=to_excel_bytes(cleaned), file_name="cleaned_sales.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)


# ───────────────────────────────────────────────────────────────────────────
# PAGE: SALES ANALYSIS
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "📊 Sales Analysis":
    st.markdown("<h1>Sales Analysis</h1>", unsafe_allow_html=True)
    

    st.markdown("<h3>Daily Sales & Moving Average</h3>", unsafe_allow_html=True)
    daily = df.set_index("Date")["Sales"].resample("D").sum().reset_index()
    daily["30D_MA"] = daily["Sales"].rolling(30).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Sales"], name="Daily Sales", opacity=0.3, line=dict(color="#3B82F6", width=1)))
    fig.add_trace(go.Scatter(x=daily["Date"], y=daily["30D_MA"], name="30-Day Moving Average", line=dict(color="#F59E0B", width=3)))
    st.plotly_chart(fig, use_container_width=True)

    
    c1, c2 = st.columns(2)
    with c1:
    
        st.markdown("<h3>Category Performance</h3>", unsafe_allow_html=True)
        cat_df = df.groupby("Category")[["Sales", "Profit"]].sum().reset_index()
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(x=cat_df["Category"], y=cat_df["Sales"], name="Sales", marker_color="#3B82F6"))
        fig_cat.add_trace(go.Bar(x=cat_df["Category"], y=cat_df["Profit"], name="Profit", marker_color="#10B981"))
        fig_cat.update_layout(barmode="group")
        st.plotly_chart(fig_cat, use_container_width=True)
    
        
    with c2:
    
        st.markdown("<h3>Regional Breakdown</h3>", unsafe_allow_html=True)
        reg_cat = df.groupby(["Region", "Category"])["Sales"].sum().reset_index()
        fig_reg = px.bar(reg_cat, x="Region", y="Sales", color="Category", barmode="group")
        st.plotly_chart(fig_reg, use_container_width=True)
    

# ───────────────────────────────────────────────────────────────────────────
# PAGE: VISUALIZATIONS
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "📈 Visualizations":
    st.markdown("<h1>Advanced Visualizations</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
    
        fig = px.histogram(df, x="Sales", nbins=40, title="Sales Value Distribution", color_discrete_sequence=["#3B82F6"])
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
    
        fig = px.box(df, x="Category", y="Sales", color="Category", title="Sales Spread by Category")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
        

    st.markdown("<h3>Sales vs Profit Scatter</h3>", unsafe_allow_html=True)
    fig_scatter = px.scatter(
        df.sample(min(5000, len(df))), x="Sales", y="Profit", 
        color="Category", size="Units_Sold", opacity=0.7
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ───────────────────────────────────────────────────────────────────────────
# PAGE: TOP PRODUCTS
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "🏆 Top Products":
    st.markdown("<h1>Top Products</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["By Revenue", "By Profitability"])
    
    with t1:
    
        prod = df.groupby("Product")["Sales"].sum().nlargest(10).reset_index().sort_values("Sales", ascending=True)
        fig = px.bar(prod, x="Sales", y="Product", orientation="h", title="Top 10 Products by Revenue", text_auto='$.2s')
        st.plotly_chart(fig, use_container_width=True)
    
        
    with t2:
    
        prof = df.groupby("Product")["Profit"].sum().nlargest(10).reset_index().sort_values("Profit", ascending=True)
        fig = px.bar(prof, x="Profit", y="Product", orientation="h", title="Top 10 Most Profitable Products", color_discrete_sequence=["#10B981"], text_auto='$.2s')
        st.plotly_chart(fig, use_container_width=True)
    

# ───────────────────────────────────────────────────────────────────────────
# PAGE: PREDICTION
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "🤖 Prediction":
    st.markdown("<h1>AI Sales Forecasting</h1>", unsafe_allow_html=True)
    

    predictor = SalesPredictor()
    if not predictor.load_model():
        with st.spinner("Training ML Model..."):
            metrics = predictor.train_model()
    else:
        metrics = predictor.train_model() # Retrain for fresh metrics on filtered data context
        
    preds = predictor.predict_future()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("MAE (Mean Absolute Error)", f"${metrics['MAE']:,.0f}")
    c2.metric("Next Month Forecast", f"${preds['Next_Month_Sales']:,.0f}")
    c3.metric("Next Quarter Forecast", f"${preds['Next_Quarter_Sales']:,.0f}")
    
    # Chart
    monthly = predictor.monthly_sales
    if monthly is not None and not monthly.empty:
        st.markdown("<h3>Regression Trend vs Actual</h3>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly["Date"], y=monthly["Sales"], name="Actual", line=dict(color="#3B82F6", width=2)))
        
        y_fit = predictor.model.predict(monthly[["Month_Index"]].values)
        fig.add_trace(go.Scatter(x=monthly["Date"], y=y_fit, name="Regression Trend", line=dict(color="#10B981", dash="dash", width=2)))
        st.plotly_chart(fig, use_container_width=True)


# ───────────────────────────────────────────────────────────────────────────
# PAGE: REPORTS
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "📄 Reports":
    st.markdown("<h1>Generate & Download Reports</h1>", unsafe_allow_html=True)
    

    st.markdown("Download the currently filtered dataset in various formats for offline analysis.")
    
    c1, c2 = st.columns(2)
    with c1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="filtered_sales.csv", mime="text/csv", use_container_width=True)
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        st.download_button("Download Excel", data=buf.getvalue(), file_name="filtered_sales.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        
    st.markdown("---")
    st.markdown("### Pre-generated PDF Report")
    report_path = Path(REPORTS_DIR) / "Sales_Report.pdf"
    if report_path.exists():
        with open(report_path, "rb") as f:
            st.download_button("Download Full PDF Report", data=f.read(), file_name="Sales_Report.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.info("PDF Report not found. Run the pipeline via CLI to generate it.")


# ───────────────────────────────────────────────────────────────────────────
# PAGE: SETTINGS
# ───────────────────────────────────────────────────────────────────────────
elif selected_page == "⚙️ Settings":
    st.markdown("<h1>Settings & Admin</h1>", unsafe_allow_html=True)
    

    st.markdown("<h3>Dataset Generation</h3>", unsafe_allow_html=True)
    if st.button("🔄 Regenerate 50k Sales Records"):
        with st.spinner("Generating new dataset..."):
            generate_sample_data()
            st.cache_data.clear()
    st.success("Dataset regenerated successfully! Please reload the app.")

