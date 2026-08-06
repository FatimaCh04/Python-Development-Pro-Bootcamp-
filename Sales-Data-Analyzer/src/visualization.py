import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
from config import CLEANED_DATA_FILE, CHARTS_DIR

logger = logging.getLogger(__name__)

# Configure professional plot aesthetics globally
sns.set_theme(style="whitegrid", context="talk", palette="deep")
plt.rcParams.update({
    'figure.dpi': 300,            # High DPI for professional reports
    'savefig.dpi': 300,
    'figure.autolayout': True,    # Automatically adjust layout so labels don't clip
    'axes.titlesize': 18,
    'axes.labelsize': 14,
    'font.family': 'sans-serif'
})

class Visualizer:
    def __init__(self, data_file=CLEANED_DATA_FILE, charts_dir=CHARTS_DIR):
        self.data_file = data_file
        self.charts_dir = Path(charts_dir)
        self.df = None

    def load_data(self):
        """Loads the cleaned dataset into memory."""
        try:
            self.df = pd.read_csv(self.data_file)
            if "Date" in self.df.columns:
                self.df["Date"] = pd.to_datetime(self.df["Date"])
            logger.info(f"Successfully loaded {len(self.df)} rows for visualization.")
        except Exception as e:
            logger.error(f"Error loading data for visualization: {e}")
            raise

    def _save_chart(self, filename: str):
        """Helper method to save charts with high DPI to the charts directory."""
        filepath = self.charts_dir / filename
        try:
            plt.tight_layout()
            plt.savefig(filepath, bbox_inches='tight')
            plt.close()
            logger.info(f"Chart saved successfully: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save chart {filename}: {e}")
            plt.close()

    def plot_monthly_sales(self):
        """Generates a Monthly Sales Line Chart."""
        if self.df is None: self.load_data()
        monthly_sales = self.df.set_index("Date")["Sales"].resample("ME").sum().reset_index()
        
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=monthly_sales, x="Date", y="Sales", marker="o", linewidth=2.5, color="#1f77b4")
        
        plt.title("Monthly Sales Trend")
        plt.xlabel("Month")
        plt.ylabel("Total Sales ($)")
        self._save_chart("monthly_sales_line.png")

    def plot_quarterly_sales(self):
        """Generates a Quarterly Sales Bar Chart."""
        if self.df is None: self.load_data()
        quarterly = self.df.set_index("Date")["Sales"].resample("QE").sum().reset_index()
        quarterly["Quarter_Label"] = quarterly["Date"].dt.to_period("Q").astype(str)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=quarterly, x="Quarter_Label", y="Sales", hue="Quarter_Label", palette="viridis", legend=False)
        
        plt.title("Quarterly Sales Performance")
        plt.xlabel("Quarter")
        plt.ylabel("Total Sales ($)")
        plt.xticks(rotation=45)
        self._save_chart("quarterly_sales_bar.png")

    def plot_category_sales(self):
        """Generates a Category Sales Bar Chart."""
        if self.df is None: self.load_data()
        category = self.df.groupby("Category")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=False)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=category, x="Category", y="Sales", hue="Category", palette="mako", legend=False)
        
        plt.title("Total Sales by Category")
        plt.xlabel("Category")
        plt.ylabel("Total Sales ($)")
        self._save_chart("category_sales_bar.png")

    def plot_region_sales(self):
        """Generates a Region Sales Pie Chart."""
        if self.df is None: self.load_data()
        region = self.df.groupby("Region")["Sales"].sum()
        
        plt.figure(figsize=(8, 8))
        colors = sns.color_palette("Set2")
        plt.pie(region, labels=region.index, autopct='%1.1f%%', startangle=140, colors=colors, 
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5})
        
        plt.title("Sales Distribution by Region")
        self._save_chart("region_sales_pie.png")

    def plot_top_products(self, top_n=10):
        """Generates a Top Products Horizontal Bar Chart."""
        if self.df is None: self.load_data()
        top_products = self.df.groupby("Product")["Sales"].sum().nlargest(top_n).reset_index()
        
        plt.figure(figsize=(12, 8))
        sns.barplot(data=top_products, x="Sales", y="Product", hue="Product", palette="rocket", legend=False)
        
        plt.title(f"Top {top_n} Products by Revenue")
        plt.xlabel("Total Sales ($)")
        plt.ylabel("")
        self._save_chart("top_products_bar.png")

    def plot_correlation_heatmap(self):
        """Generates a Correlation Heatmap."""
        if self.df is None: self.load_data()
        numeric_df = self.df.select_dtypes(include=['float64', 'int64'])
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", 
                    linewidths=1, square=True, cbar_kws={"shrink": .8})
        
        plt.title("Correlation Matrix of Numeric Features")
        self._save_chart("correlation_heatmap.png")

    def plot_scatter(self):
        """Generates a Scatter Plot (Sales vs Profit)."""
        if self.df is None: self.load_data()
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=self.df, x="Sales", y="Profit", hue="Category", alpha=0.7, palette="tab10")
        
        plt.title("Sales vs Profit Analysis")
        plt.xlabel("Sales ($)")
        plt.ylabel("Profit ($)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        self._save_chart("scatter_plot.png")

    def plot_histogram(self):
        """Generates a standard Histogram for Sales."""
        if self.df is None: self.load_data()
        
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df["Sales"], bins=40, kde=True, color="#9b59b6", line_kws={'linewidth': 2})
        
        plt.title("Sales Amount Distribution")
        plt.xlabel("Sales ($)")
        plt.ylabel("Frequency")
        self._save_chart("histogram.png")

    def plot_profit_distribution(self):
        """Generates a Profit Distribution Plot."""
        if self.df is None: self.load_data()
        
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df["Profit"], bins=40, kde=True, color="#2ecc71", line_kws={'linewidth': 2})
        
        plt.title("Profit Amount Distribution")
        plt.xlabel("Profit ($)")
        plt.ylabel("Frequency")
        self._save_chart("profit_distribution.png")

    def plot_moving_averages(self):
        """Generates a Moving Average Trend with Rolling Mean and Rolling Median."""
        if self.df is None: self.load_data()
        daily = self.df.set_index("Date")["Sales"].resample("D").sum()
        
        # 30-Day Rolling Calculations
        rolling_mean = daily.rolling(window=30, min_periods=1).mean()
        rolling_median = daily.rolling(window=30, min_periods=1).median()
        
        plt.figure(figsize=(14, 7))
        # Plot raw daily sales very lightly in the background
        plt.plot(daily.index, daily, label="Daily Sales", alpha=0.2, color="gray")
        
        # Plot Moving Averages
        plt.plot(rolling_mean.index, rolling_mean, label="30-Day Rolling Mean", color="#e74c3c", linewidth=2.5)
        plt.plot(rolling_median.index, rolling_median, label="30-Day Rolling Median", color="#3498db", linewidth=2.5, linestyle="--")
        
        plt.title("Moving Average Trend Analysis")
        plt.xlabel("Date")
        plt.ylabel("Daily Sales ($)")
        plt.legend()
        self._save_chart("moving_average_trend.png")

    def generate_all_charts(self):
        """Main execution method to run all chart generations."""
        logger.info("Initializing chart generation process...")
        self.load_data()
        
        self.plot_monthly_sales()
        self.plot_quarterly_sales()
        self.plot_category_sales()
        self.plot_region_sales()
        self.plot_top_products()
        self.plot_correlation_heatmap()
        self.plot_scatter()
        self.plot_histogram()
        self.plot_profit_distribution()
        self.plot_moving_averages()
        
        logger.info("All professional visualizations have been successfully generated and saved.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    vis = Visualizer()
    vis.generate_all_charts()
