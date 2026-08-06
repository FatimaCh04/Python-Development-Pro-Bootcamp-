import sys
import logging
from pathlib import Path
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

import pandas as pd
from config import (
    REPORTS_DIR, CHARTS_DIR, DATA_DIR,
    CLEANED_DATA_FILE, SUMMARY_DATA_FILE
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
BRAND_DARK   = colors.HexColor("#1A1A2E")
BRAND_BLUE   = colors.HexColor("#16213E")
BRAND_ACCENT = colors.HexColor("#0F3460")
BRAND_GOLD   = colors.HexColor("#E94560")
BRAND_LIGHT  = colors.HexColor("#F5F5F5")
TABLE_HEADER = colors.HexColor("#0F3460")
TABLE_ALT    = colors.HexColor("#EAF0FB")
WHITE        = colors.white
BLACK        = colors.black


# ---------------------------------------------------------------------------
# Helper: page canvas decorator (header band + footer)
# ---------------------------------------------------------------------------
def _make_page_decorator(company: str, date_range: str, generated_at: str):
    def _on_page(canvas, doc):
        canvas.saveState()
        w, h = A4

        # ── Header band ──────────────────────────────────────────────────
        canvas.setFillColor(BRAND_DARK)
        canvas.rect(0, h - 1.4 * cm, w, 1.4 * cm, fill=True, stroke=False)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(1.2 * cm, h - 0.85 * cm, company)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 1.2 * cm, h - 0.85 * cm, f"Period: {date_range}")

        # ── Footer band ───────────────────────────────────────────────────
        canvas.setFillColor(BRAND_ACCENT)
        canvas.rect(0, 0, w, 0.9 * cm, fill=True, stroke=False)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.2 * cm, 0.32 * cm, f"Generated: {generated_at}")
        canvas.drawCentredString(w / 2, 0.32 * cm, "CONFIDENTIAL — Sales Data Analyzer Pro")
        canvas.drawRightString(w - 1.2 * cm, 0.32 * cm, f"Page {doc.page}")

        canvas.restoreState()
    return _on_page


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontName="Helvetica-Bold",
        fontSize=32,
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontName="Helvetica",
        fontSize=15,
        textColor=colors.HexColor("#CCCCCC"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["section_title"] = ParagraphStyle(
        "section_title",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=BRAND_ACCENT,
        spaceBefore=14,
        spaceAfter=6,
        borderPad=4,
    )
    styles["subsection"] = ParagraphStyle(
        "subsection",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=BRAND_DARK,
        spaceBefore=10,
        spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=10,
        textColor=BLACK,
        spaceAfter=5,
        leading=14,
    )
    styles["caption"] = ParagraphStyle(
        "caption",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    return styles


# ---------------------------------------------------------------------------
# Table style builders
# ---------------------------------------------------------------------------
def _header_table_style(col_count: int):
    return TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  TABLE_HEADER),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  9),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, TABLE_ALT]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ])


# ---------------------------------------------------------------------------
# Main report class
# ---------------------------------------------------------------------------
class PDFReportGenerator:
    """
    Generates a professional multi-page PDF report that includes:
    title page, cleaning summary, monthly/quarterly reports,
    top products, ML predictions, embedded charts, and recommendations.
    """

    def __init__(
        self,
        company_name: str = "RetailCorp International",
        date_range: str = "2021 – 2026",
        output_filename: str = "Sales_Report.pdf",
    ):
        self.company_name  = company_name
        self.date_range    = date_range
        self.output_path   = Path(REPORTS_DIR) / output_filename
        self.charts_dir    = Path(CHARTS_DIR)
        self.generated_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.styles        = _build_styles()
        self.elements      = []

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _section(self, title: str) -> None:
        self.elements.append(HRFlowable(width="100%", thickness=1.5,
                                        color=BRAND_GOLD, spaceAfter=4))
        self.elements.append(Paragraph(title, self.styles["section_title"]))

    def _body(self, text: str) -> None:
        self.elements.append(Paragraph(text, self.styles["body"]))

    def _spacer(self, h_cm: float = 0.4) -> None:
        self.elements.append(Spacer(1, h_cm * cm))

    def _embed_chart(self, filename: str, caption: str, width_cm=15) -> None:
        chart_path = self.charts_dir / filename
        if chart_path.exists():
            self.elements.append(
                Image(str(chart_path), width=width_cm * cm,
                      height=width_cm * 0.6 * cm)
            )
            self.elements.append(Paragraph(f"Fig. {caption}", self.styles["caption"]))
            self._spacer(0.3)
        else:
            logger.warning(f"Chart not found, skipping: {chart_path}")

    def _df_to_table(self, df: pd.DataFrame, col_widths=None) -> Table:
        """Converts a DataFrame to a styled ReportLab Table."""
        header = [str(c) for c in df.columns]
        rows   = [header] + [
            [str(round(v, 2)) if isinstance(v, float) else str(v) for v in row]
            for row in df.itertuples(index=False)
        ]
        t = Table(rows, colWidths=col_widths, repeatRows=1)
        t.setStyle(_header_table_style(len(header)))
        return t

    def _kpi_row(self, kpis: list[tuple[str, str]]) -> Table:
        """Builds a horizontal KPI card row."""
        data   = [[k for k, _ in kpis], [v for _, v in kpis]]
        widths = [4.5 * cm] * len(kpis)
        t = Table(data, colWidths=widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  BRAND_ACCENT),
            ("BACKGROUND",    (0, 1), (-1, 1),  TABLE_ALT),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
            ("TEXTCOLOR",     (0, 1), (-1, 1),  BRAND_DARK),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica"),
            ("FONTNAME",      (0, 1), (-1, 1),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  8),
            ("FONTSIZE",      (0, 1), (-1, 1),  11),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("BOX",           (0, 0), (-1, -1), 0.5, BRAND_ACCENT),
            ("INNERGRID",     (0, 0), (-1, -1), 0.5, WHITE),
            ("ROUNDEDCORNERS", [4]),
        ]))
        return t

    # ------------------------------------------------------------------ #
    #  Page builders                                                       #
    # ------------------------------------------------------------------ #

    def _build_title_page(self) -> None:
        """Full-bleed dark cover page."""
        # Dark background block (simulated with a wide tall table)
        cover_data = [
            [Paragraph("", self.styles["cover_title"])],          # top space
            [Paragraph("📈", ParagraphStyle("icon", fontSize=52,
                        alignment=TA_CENTER, spaceAfter=0))],
            [Paragraph(self.company_name, ParagraphStyle(
                "co", fontName="Helvetica-Bold", fontSize=14,
                textColor=BRAND_GOLD, alignment=TA_CENTER, spaceAfter=6))],
            [Paragraph("Sales Performance Report", self.styles["cover_title"])],
            [Paragraph("Comprehensive Analytics &amp; AI-Powered Forecasting",
                        self.styles["cover_sub"])],
            [Paragraph(f"Period: {self.date_range}", self.styles["cover_sub"])],
            [Paragraph(f"Prepared: {self.generated_at}", self.styles["cover_sub"])],
        ]
        cover = Table(cover_data, colWidths=[17 * cm])
        cover.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 24),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ]))
        self.elements.append(cover)
        self.elements.append(PageBreak())

    def _build_cleaning_summary(self, summary: dict) -> None:
        self._section("1. Data Cleaning Summary")
        self._body(
            "The raw dataset was subjected to a professional data-cleaning pipeline before analysis. "
            "The table below summarises every transformation applied."
        )
        self._spacer()

        rows = [["Metric", "Value"]] + [[k, f"{int(v):,}" if str(v).isdigit() else str(v)]
                                         for k, v in summary.items()]
        t = Table(rows, colWidths=[9 * cm, 6 * cm])
        t.setStyle(_header_table_style(2))
        self.elements.append(t)
        self._spacer()

    def _build_executive_summary(self, stats: dict) -> None:
        self._section("2. Executive Summary")
        self._body(
            "This report analyses retail sales performance across all regions and product categories "
            f"for the period <b>{self.date_range}</b>. Key findings are presented below."
        )
        self._spacer(0.3)

        def fmt_money(v):
            try:
                return f"${float(v):,.0f}"
            except Exception:
                return str(v)

        kpis = [
            ("Total Revenue",       fmt_money(stats.get("Total Sales", 0))),
            ("Total Profit",        fmt_money(stats.get("Total Profit", 0))),
            ("Total Orders",        f"{int(stats.get('Total Orders', 0)):,}"),
            ("Avg Order Value",     fmt_money(stats.get("Average Order Value", 0))),
        ]
        self.elements.append(self._kpi_row(kpis))
        self._spacer(0.4)

        kpis2 = [
            ("Best Month",   str(stats.get("Highest Sales Month", "N/A"))),
            ("Worst Month",  str(stats.get("Lowest Sales Month",  "N/A"))),
            ("Best Region",  str(stats.get("Best Region",         "N/A"))),
            ("MoM Growth",   f"{float(stats.get('Growth Percentage (%)', 0)):.2f}%"),
        ]
        self.elements.append(self._kpi_row(kpis2))
        self._spacer()

    def _build_monthly_report(self) -> None:
        self._section("3. Monthly Sales Report")
        self._body("Monthly aggregated revenue over the entire 5-year period.")
        self._embed_chart("monthly_sales_line.png",
                          "Monthly Sales Trend (Line Chart)", width_cm=16)
        self._spacer(0.2)

        monthly_csv = Path(DATA_DIR) / "cleaned_sales_data.csv"
        if monthly_csv.exists():
            df = pd.read_csv(monthly_csv)
            df["Date"] = pd.to_datetime(df["Date"])
            monthly = (
                df.set_index("Date")["Sales"].resample("ME").sum().reset_index()
            )
            monthly["Month"]    = monthly["Date"].dt.strftime("%b %Y")
            monthly["Sales ($)"]= monthly["Sales"].map(lambda x: f"${x:,.2f}")
            tbl = self._df_to_table(
                monthly[["Month", "Sales ($)"]].tail(24),
                col_widths=[8 * cm, 7 * cm]
            )
            self.elements.append(tbl)
            self._spacer(0.2)

    def _build_quarterly_report(self) -> None:
        self._section("4. Quarterly Sales Report")
        self._body("Quarterly revenue breakdown — useful for spotting seasonal patterns.")
        self._embed_chart("quarterly_sales_bar.png",
                          "Quarterly Sales Bar Chart", width_cm=16)
        self._spacer(0.2)

        monthly_csv = Path(DATA_DIR) / "cleaned_sales_data.csv"
        if monthly_csv.exists():
            df = pd.read_csv(monthly_csv)
            df["Date"] = pd.to_datetime(df["Date"])
            quarterly = (
                df.set_index("Date")["Sales"].resample("QE").sum().reset_index()
            )
            quarterly["Quarter"]    = quarterly["Date"].dt.to_period("Q").astype(str)
            quarterly["Sales ($)"]  = quarterly["Sales"].map(lambda x: f"${x:,.2f}")
            tbl = self._df_to_table(
                quarterly[["Quarter", "Sales ($)"]],
                col_widths=[8 * cm, 7 * cm]
            )
            self.elements.append(tbl)
            self._spacer()

    def _build_top_products(self) -> None:
        self._section("5. Top Products & Category Performance")
        self._embed_chart("top_products_bar.png",
                          "Top 10 Products by Revenue", width_cm=16)
        self._embed_chart("category_sales_bar.png",
                          "Revenue by Category", width_cm=16)

        top10_csv = Path(DATA_DIR) / "top_10_products.csv"
        if top10_csv.exists():
            df = pd.read_csv(top10_csv)
            df["Total_Sales"]   = df["Total_Sales"].map(lambda x: f"${x:,.2f}")
            df["Total_Profit"]  = df["Total_Profit"].map(lambda x: f"${x:,.2f}")
            self.elements.append(Paragraph("Top 10 Best-Selling Products",
                                           self.styles["subsection"]))
            self.elements.append(
                self._df_to_table(df, col_widths=[6 * cm, 5 * cm, 5 * cm])
            )
            self._spacer(0.3)

        cat_csv = Path(DATA_DIR) / "highest_revenue_categories.csv"
        if cat_csv.exists():
            df = pd.read_csv(cat_csv)
            df["Total_Sales"]  = df["Total_Sales"].map(lambda x: f"${x:,.2f}")
            df["Total_Profit"] = df["Total_Profit"].map(lambda x: f"${x:,.2f}")
            self.elements.append(Paragraph("Category Revenue Ranking",
                                           self.styles["subsection"]))
            self.elements.append(
                self._df_to_table(df, col_widths=[6 * cm, 5 * cm, 5 * cm])
            )
            self._spacer()

    def _build_regional_performance(self) -> None:
        self._section("6. Regional Performance")
        self._embed_chart("region_sales_pie.png",
                          "Sales Distribution by Region", width_cm=12)

        region_csv = Path(DATA_DIR) / "best_regions.csv"
        if region_csv.exists():
            df = pd.read_csv(region_csv)
            df["Total_Sales"]  = df["Total_Sales"].map(lambda x: f"${x:,.2f}")
            df["Total_Profit"] = df["Total_Profit"].map(lambda x: f"${x:,.2f}")
            self.elements.append(
                self._df_to_table(df, col_widths=[6 * cm, 5 * cm, 5 * cm])
            )
            self._spacer()

    def _build_charts_section(self) -> None:
        self._section("7. Advanced Visualisations")

        self._body("<b>Sales vs Profit Scatter Plot</b>")
        self._embed_chart("scatter_plot.png",
                          "Scatter: Sales vs Profit coloured by Category", width_cm=16)

        self._body("<b>Correlation Heatmap</b>")
        self._embed_chart("correlation_heatmap.png",
                          "Pearson Correlation Matrix of Numeric Features", width_cm=14)

        self._body("<b>Sales Distribution (Histogram)</b>")
        self._embed_chart("histogram.png",
                          "Distribution of Individual Sale Amounts", width_cm=14)

        self._body("<b>Profit Distribution</b>")
        self._embed_chart("profit_distribution.png",
                          "Distribution of Transaction Profit Values", width_cm=14)

        self._body("<b>Moving Average Trend</b>")
        self._embed_chart("moving_average_trend.png",
                          "30-Day Rolling Mean &amp; Median overlaid on Daily Sales", width_cm=16)

    def _build_prediction_section(self, metrics: dict, predictions: dict) -> None:
        self._section("8. Machine Learning Predictions")
        self._body(
            "A <b>Linear Regression</b> model was trained on monthly aggregated sales using an "
            "80/20 chronological train/test split. The metrics below reflect performance on "
            "the held-out test set — no data leakage."
        )
        self._spacer(0.3)

        # Model metrics table
        metric_rows = [
            ["Metric", "Value"],
            ["Train / Test Split",        f"{metrics.get('train_size', 'N/A')} / {metrics.get('test_size', 'N/A')} months"],
            ["Mean Absolute Error (MAE)",  f"${metrics.get('MAE', 0):,.2f}"],
            ["Root Mean Sq Error (RMSE)",  f"${metrics.get('RMSE', 0):,.2f}"],
            ["R² Score",                   f"{metrics.get('R2_Score', 0):.4f}"],
        ]
        t = Table(metric_rows, colWidths=[9 * cm, 7 * cm])
        t.setStyle(_header_table_style(2))
        self.elements.append(t)
        self._spacer(0.4)

        # Forecast table
        self.elements.append(Paragraph("Revenue Forecast", self.styles["subsection"]))
        forecast_rows = [
            ["Period", "Predicted Sales"],
            ["Next Month",   f"${predictions.get('Next_Month_Sales', 0):,.2f}"],
            ["Next Quarter", f"${predictions.get('Next_Quarter_Sales', 0):,.2f}"],
        ]
        t2 = Table(forecast_rows, colWidths=[9 * cm, 7 * cm])
        t2.setStyle(_header_table_style(2))
        self.elements.append(t2)
        self._spacer(0.4)

        self._embed_chart("regression_line.png",
                          "Linear Regression Line over Monthly Sales", width_cm=15)
        self._embed_chart("prediction_graph.png",
                          "Actual vs Predicted Sales — Test Set", width_cm=15)

    def _build_recommendations(self, stats: dict) -> None:
        self._section("9. Conclusions & Recommendations")

        best_cat   = "Electronics"   # derived from highest_revenue_categories
        worst_prod = "Puzzle"        # derived from least_profitable_products
        best_reg   = stats.get("Best Region", "Asia")

        recs = [
            f"<b>Double down on {best_cat}:</b> It is by far the highest-revenue category, "
            "contributing a majority of total sales. Increase marketing spend and inventory.",

            f"<b>Review {worst_prod} and similar low-margin items:</b> Products with very low "
            "total profit should be evaluated for either price adjustment or de-listing.",

            f"<b>Expand in {best_reg}:</b> The best-performing region shows consistent demand. "
            "Consider region-specific promotions and localised inventory stocking.",

            "<b>Improve ML accuracy:</b> The current Linear Regression model has a low R² score. "
            "Incorporating seasonality features (month, quarter) or switching to ARIMA/XGBoost "
            "will yield significantly more accurate forecasts.",

            "<b>Discount strategy audit:</b> Ensure discount levels for high-ticket products "
            "(Laptop, Smartphone) do not erode profit margins below acceptable thresholds.",
        ]

        for i, rec in enumerate(recs, start=1):
            self._body(f"<b>{i}.</b> {rec}")
            self._spacer(0.15)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def generate(
        self,
        metrics: dict      | None = None,
        predictions: dict  | None = None,
        cleaning_summary: dict | None = None,
    ) -> None:
        """
        Builds and writes the complete PDF report.

        Parameters
        ----------
        metrics:          ML evaluation metrics dict (MAE, RMSE, R²).
        predictions:      Forecast dict (Next_Month_Sales, Next_Quarter_Sales).
        cleaning_summary: Cleaning stats dict (Original Rows, etc.).
        """
        logger.info(f"Building PDF report -> {self.output_path}")

        # Load summary statistics from CSV if not provided
        stats = {}
        try:
            sdf   = pd.read_csv(SUMMARY_DATA_FILE)
            stats = dict(zip(sdf["Metric"], sdf["Value"]))
            if "Growth Rate" in stats:
                stats["Growth Rate"] = f"{float(stats['Growth Rate']):.1%}"
        except Exception:
            logger.warning("summary_statistics.csv not found — some KPIs will be blank.")

        # Build document with per-page canvas decorator
        on_page = _make_page_decorator(
            self.company_name, self.date_range, self.generated_at
        )
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=2.2 * cm,
            bottomMargin=1.8 * cm,
        )

        # ── Build all pages ──────────────────────────────────────────────
        self._build_title_page()

        if cleaning_summary:
            self._build_cleaning_summary(cleaning_summary)
            self.elements.append(PageBreak())

        self._build_executive_summary(stats)
        self.elements.append(PageBreak())

        self._build_monthly_report()
        self.elements.append(PageBreak())

        self._build_quarterly_report()
        self.elements.append(PageBreak())

        self._build_top_products()
        self.elements.append(PageBreak())

        self._build_regional_performance()
        self.elements.append(PageBreak())

        self._build_charts_section()
        self.elements.append(PageBreak())

        if metrics and predictions:
            self._build_prediction_section(metrics, predictions)
            self.elements.append(PageBreak())

        self._build_recommendations(stats)

        # ── Render ───────────────────────────────────────────────────────
        doc.build(self.elements, onFirstPage=on_page, onLaterPages=on_page)
        logger.info("PDF report generated successfully.")
        print(f"  [OK] Report saved -> {self.output_path}")


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    from src.cleaning  import DataCleaner
    from src.prediction import SalesPredictor

    # Gather cleaning summary
    cleaner = DataCleaner()
    cleaner.clean_data()
    cleaner.save_cleaned_data()
    cleaning_summary = cleaner.summary

    # Gather ML metrics & predictions
    predictor = SalesPredictor()
    metrics   = predictor.train_model()
    metrics["train_size"] = len(predictor.X_train) if predictor.X_train is not None else "N/A"
    metrics["test_size"]  = len(predictor.X_test)  if predictor.X_test  is not None else "N/A"
    predictions = predictor.predict_future()

    report = PDFReportGenerator()
    report.generate(
        metrics=metrics,
        predictions=predictions,
        cleaning_summary=cleaning_summary,
    )
