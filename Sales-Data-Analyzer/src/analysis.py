import pandas as pd
import logging
from pathlib import Path
from config import CLEANED_DATA_FILE, SUMMARY_DATA_FILE, DATA_DIR

logger = logging.getLogger(__name__)

class DataAnalyzer:
    def __init__(self, data_file=CLEANED_DATA_FILE):
        self.data_file = data_file
        self.df = None
        
        # Results stored as DataFrames
        self.daily_sales = pd.DataFrame()
        self.weekly_sales = pd.DataFrame()
        self.monthly_sales = pd.DataFrame()
        self.quarterly_sales = pd.DataFrame()
        self.yearly_sales = pd.DataFrame()
        self.region_wise_sales = pd.DataFrame()
        self.category_wise_sales = pd.DataFrame()
        self.product_wise_sales = pd.DataFrame()
        self.customer_spending = pd.DataFrame()

        # Ranked product / category / region tables
        self.top_5_products = pd.DataFrame()
        self.top_10_products = pd.DataFrame()
        self.most_profitable_products = pd.DataFrame()
        self.least_profitable_products = pd.DataFrame()
        self.highest_revenue_categories = pd.DataFrame()
        self.best_regions = pd.DataFrame()

        # Summary scalar results
        self.summary_stats = {}

    def load_data(self):
        """Loads the cleaned dataset into memory and ensures correct data types."""
        try:
            self.df = pd.read_csv(self.data_file)
            self.df["Date"] = pd.to_datetime(self.df["Date"])
            logger.info(f"Loaded {len(self.df)} rows from {self.data_file} for analysis.")
        except Exception as e:
            logger.error(f"Failed to load data for analysis: {e}")
            raise

    def generate_time_series_sales(self):
        """Generates Daily, Weekly, Monthly, Quarterly, and Yearly sales DataFrames."""
        df_time = self.df.set_index("Date")
        
        # Use 'ME', 'QE', 'YE' for pandas >= 2.2 compatibility, 'W' for weekly
        self.daily_sales = df_time["Sales"].resample("D").sum().reset_index()
        self.weekly_sales = df_time["Sales"].resample("W").sum().reset_index()
        self.monthly_sales = df_time["Sales"].resample("ME").sum().reset_index()
        self.quarterly_sales = df_time["Sales"].resample("QE").sum().reset_index()
        self.yearly_sales = df_time["Sales"].resample("YE").sum().reset_index()
        
        logger.info("Generated time-series sales DataFrames (Daily, Weekly, Monthly, Quarterly, Yearly).")

    def generate_categorical_sales(self):
        """Generates Region, Category, Product, and Customer specific sales DataFrames."""
        self.region_wise_sales = self.df.groupby("Region", as_index=False)["Sales"].sum().sort_values(by="Sales", ascending=False)
        self.category_wise_sales = self.df.groupby("Category", as_index=False)["Sales"].sum().sort_values(by="Sales", ascending=False)
        self.product_wise_sales = self.df.groupby("Product", as_index=False)["Sales"].sum().sort_values(by="Sales", ascending=False)
        self.customer_spending = self.df.groupby("Customer", as_index=False)["Sales"].sum().sort_values(by="Sales", ascending=False)
        
        logger.info("Generated categorical sales DataFrames (Region, Category, Product, Customer).")

    def calculate_growth_percentage(self):
        """Calculates Month-over-Month growth percentage based on monthly sales."""
        if self.monthly_sales.empty:
            return 0.0
        
        # Ensure it's sorted by date
        df_m = self.monthly_sales.sort_values("Date")
        if len(df_m) < 2:
            return 0.0
            
        last_month = df_m.iloc[-1]["Sales"]
        prev_month = df_m.iloc[-2]["Sales"]
        
        if prev_month == 0:
            return 100.0 if last_month > 0 else 0.0
            
        growth_pct = ((last_month - prev_month) / prev_month) * 100
        return round(growth_pct, 2)

    def generate_summary_metrics(self):
        """Generates key performance indicators and comparative metrics."""
        total_sales = self.df["Sales"].sum()
        total_orders = len(self.df)
        
        # Averages
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # High/Low Month
        # We can extract from monthly_sales dataframe directly
        if not self.monthly_sales.empty:
            best_month_idx = self.monthly_sales["Sales"].idxmax()
            worst_month_idx = self.monthly_sales["Sales"].idxmin()
            best_month = self.monthly_sales.loc[best_month_idx, "Date"].strftime('%Y-%m')
            worst_month = self.monthly_sales.loc[worst_month_idx, "Date"].strftime('%Y-%m')
        else:
            best_month, worst_month = "N/A", "N/A"

        # Best/Worst Region
        if not self.region_wise_sales.empty:
            best_region = self.region_wise_sales.iloc[0]["Region"]
            worst_region = self.region_wise_sales.iloc[-1]["Region"]
        else:
            best_region, worst_region = "N/A", "N/A"

        # Growth Percentage
        growth_pct = self.calculate_growth_percentage()

        self.summary_stats = {
            "Total Sales": total_sales,
            "Total Profit": self.df["Profit"].sum() if "Profit" in self.df.columns else 0,
            "Total Orders": total_orders,
            "Average Order Value": avg_order_value,
            "Growth Percentage (%)": growth_pct,
            "Highest Sales Month": best_month,
            "Lowest Sales Month": worst_month,
            "Best Region": best_region,
            "Worst Region": worst_region
        }
        logger.info("Generated summary performance metrics.")

    def analyze(self):
        """Main execution method to run all analyses."""
        if self.df is None:
            self.load_data()
            
        logger.info("Starting data analysis pipeline...")
        self.generate_time_series_sales()
        self.generate_categorical_sales()
        self.generate_summary_metrics()
        self.generate_rankings()
        self.display_rankings()
        self.save_rankings_to_csv()

        # Save scalar summary statistics to CSV
        try:
            summary_df = pd.DataFrame(list(self.summary_stats.items()), columns=["Metric", "Value"])
            summary_df.to_csv(SUMMARY_DATA_FILE, index=False)
            logger.info(f"Exported summary statistics to {SUMMARY_DATA_FILE}")
        except Exception as e:
            logger.error(f"Failed to export summary statistics: {e}")

        logger.info("Data analysis pipeline completed successfully.")
        return self.summary_stats

    def generate_rankings(self):
        """Generates ranked tables for products, categories, and regions."""
        # Aggregate sales and profit per product from raw records
        product_agg = (
            self.df.groupby("Product", as_index=False)
            .agg(Total_Sales=("Sales", "sum"), Total_Profit=("Profit", "sum"))
        )

        # Top 5 and Top 10 best-selling products (sorted by Total_Sales descending)
        self.top_5_products = (
            product_agg.sort_values("Total_Sales", ascending=False)
            .head(5)
            .reset_index(drop=True)
        )
        self.top_10_products = (
            product_agg.sort_values("Total_Sales", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )

        # Most profitable products (sorted by Total_Profit descending)
        self.most_profitable_products = (
            product_agg.sort_values("Total_Profit", ascending=False)
            .head(10)
            .reset_index(drop=True)
        )

        # Least profitable products (sorted by Total_Profit ascending)
        self.least_profitable_products = (
            product_agg.sort_values("Total_Profit", ascending=True)
            .head(10)
            .reset_index(drop=True)
        )

        # Highest revenue categories (sorted by Total_Sales descending)
        self.highest_revenue_categories = (
            self.df.groupby("Category", as_index=False)
            .agg(Total_Sales=("Sales", "sum"), Total_Profit=("Profit", "sum"))
            .sort_values("Total_Sales", ascending=False)
            .reset_index(drop=True)
        )

        # Best regions (sorted by Total_Sales descending)
        self.best_regions = (
            self.df.groupby("Region", as_index=False)
            .agg(Total_Sales=("Sales", "sum"), Total_Profit=("Profit", "sum"))
            .sort_values("Total_Sales", ascending=False)
            .reset_index(drop=True)
        )

        logger.info("Generated all ranked product, category, and region tables.")

    def display_rankings(self):
        """Prints all ranking tables neatly to the console."""
        tables = [
            ("Top 5 Best-Selling Products",    self.top_5_products),
            ("Top 10 Best-Selling Products",   self.top_10_products),
            ("Most Profitable Products",        self.most_profitable_products),
            ("Least Profitable Products",       self.least_profitable_products),
            ("Highest Revenue Categories",      self.highest_revenue_categories),
            ("Best Regions",                    self.best_regions),
        ]
        for title, df in tables:
            print(f"\n{'='*50}")
            print(f"  {title}")
            print('='*50)
            print(df.to_string(index=False))

    def save_rankings_to_csv(self):
        """Saves every ranked table as its own CSV file inside data/."""
        exports = {
            "top_5_products.csv":             self.top_5_products,
            "top_10_products.csv":            self.top_10_products,
            "most_profitable_products.csv":   self.most_profitable_products,
            "least_profitable_products.csv":  self.least_profitable_products,
            "highest_revenue_categories.csv": self.highest_revenue_categories,
            "best_regions.csv":               self.best_regions,
        }
        for filename, df in exports.items():
            filepath = Path(DATA_DIR) / filename
            try:
                df.to_csv(filepath, index=False)
                logger.info(f"Saved ranking table to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save {filename}: {e}")

    # Utility getters for specific requirements
    def get_top_products(self, n: int = 10) -> pd.DataFrame:
        """Returns the top N products by total sales."""
        return self.product_wise_sales.head(n)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    analyzer = DataAnalyzer()
    stats = analyzer.analyze()
    print("\n--- Summary Statistics ---")
    for key, val in stats.items():
        print(f"{key}: {val}")
