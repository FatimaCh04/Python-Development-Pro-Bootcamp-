import pandas as pd
import numpy as np
import logging
from config import RAW_DATA_FILE, CLEANED_DATA_FILE

# Configure module-level logging
logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, input_file=RAW_DATA_FILE, output_file=CLEANED_DATA_FILE):
        self.input_file = input_file
        self.output_file = output_file
        self.df = None
        self.summary = {
            "Original Rows": 0,
            "Rows Removed": 0,
            "Duplicates Removed": 0,
            "Missing Values Filled": 0,
            "Final Rows": 0
        }

    def load_data(self):
        """Reads the raw dataset from the CSV file."""
        try:
            self.df = pd.read_csv(self.input_file)
            self.summary["Original Rows"] = len(self.df)
            logger.info(f"Successfully loaded {self.summary['Original Rows']} rows from {self.input_file}")
        except FileNotFoundError:
            logger.error(f"Error: The file {self.input_file} was not found.")
            raise
        except pd.errors.EmptyDataError:
            logger.error(f"Error: The file {self.input_file} is empty.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading data: {e}")
            raise

    def clean_data(self):
        """Executes the data cleaning pipeline."""
        if self.df is None:
            self.load_data()

        logger.info("Initiating professional data cleaning pipeline...")
        
        # 1. Handle Duplicate Rows
        duplicates_count = self.df.duplicated().sum()
        if duplicates_count > 0:
            self.df = self.df.drop_duplicates()
            self.summary["Duplicates Removed"] = duplicates_count
            logger.info(f"Removed {duplicates_count} duplicate rows.")

        # 2. Handle Missing Values
        missing_count_before = self.df.isna().sum().sum()
        if missing_count_before > 0:
            # Fill missing categorical/string columns
            string_cols = ["Product", "Category", "Region", "Customer", "Salesperson", "Payment_Method"]
            for col in string_cols:
                if col in self.df.columns:
                    self.df[col] = self.df[col].fillna("Unknown")
            
            # Fill numeric columns with medians
            numeric_cols = ["Units_Sold", "Unit_Price", "Discount"]
            for col in numeric_cols:
                if col in self.df.columns:
                    median_val = self.df[col].median()
                    self.df[col] = self.df[col].fillna(median_val)
                    
            missing_count_after = self.df.isna().sum().sum()
            self.summary["Missing Values Filled"] = int(missing_count_before - missing_count_after)
            logger.info(f"Filled {self.summary['Missing Values Filled']} missing values.")

        # 3. Convert Data Types & Fix Invalid Dates
        try:
            if "Date" in self.df.columns:
                self.df["Date"] = pd.to_datetime(self.df["Date"], errors='coerce')
                # Drop rows where dates couldn't be parsed
                invalid_dates_count = self.df["Date"].isna().sum()
                if invalid_dates_count > 0:
                    self.df = self.df.dropna(subset=["Date"])
                    logger.info(f"Removed {invalid_dates_count} rows with unparseable/invalid dates.")
        except Exception as e:
            logger.error(f"Error parsing dates: {e}")

        # 4. Remove Negative Sales and Impossible Values
        # Ensure correct datatypes for numeric filtering
        numeric_validation_cols = ["Units_Sold", "Unit_Price", "Sales", "Cost"]
        for col in numeric_validation_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Drop rows where conversion to numeric failed
        nan_numeric_count = self.df[numeric_validation_cols].isna().any(axis=1).sum()
        if nan_numeric_count > 0:
            self.df = self.df.dropna(subset=numeric_validation_cols)
            logger.info(f"Removed {nan_numeric_count} rows containing non-numeric corrupt values.")

        # Remove negative or impossible (zero) values where they shouldn't exist
        rows_before_filter = len(self.df)
        self.df = self.df[
            (self.df["Units_Sold"] > 0) & 
            (self.df["Unit_Price"] > 0) & 
            (self.df["Sales"] > 0) & 
            (self.df["Cost"] >= 0)
        ]
        impossible_values_removed = rows_before_filter - len(self.df)
        if impossible_values_removed > 0:
            logger.info(f"Removed {impossible_values_removed} rows with negative or impossible numeric values.")

        # 5. Recalculate derived columns to ensure integrity
        if all(col in self.df.columns for col in ["Units_Sold", "Unit_Price", "Discount"]):
            self.df["Sales"] = (self.df["Units_Sold"] * self.df["Unit_Price"] * (1 - self.df["Discount"])).round(2)
        if "Sales" in self.df.columns and "Cost" in self.df.columns:
            self.df["Profit"] = (self.df["Sales"] - self.df["Cost"]).round(2)

        # Reconstruct Time features based on the cleaned Date column
        if "Date" in self.df.columns:
            self.df["Month"] = self.df["Date"].dt.month
            self.df["Quarter"] = self.df["Date"].dt.quarter
            self.df["Year"] = self.df["Date"].dt.year

        # Finalize Summary Metrics
        self.summary["Final Rows"] = len(self.df)
        self.summary["Rows Removed"] = self.summary["Original Rows"] - self.summary["Final Rows"]

        logger.info("Data cleaning pipeline completed.")
        self.display_summary()
        
        return self.df

    def display_summary(self):
        """Displays the required cleaning summary metrics."""
        print("\n" + "="*30)
        print("    DATA CLEANING SUMMARY")
        print("="*30)
        print(f"Original Rows         : {self.summary['Original Rows']}")
        print(f"Rows Removed          : {self.summary['Rows Removed']}")
        print(f"Duplicates Removed    : {self.summary['Duplicates Removed']}")
        print(f"Missing Values Filled : {self.summary['Missing Values Filled']}")
        print(f"Final Rows            : {self.summary['Final Rows']}")
        print("="*30 + "\n")

    def save_cleaned_data(self):
        """Saves the cleaned dataset to a CSV file."""
        try:
            if self.df is not None and not self.df.empty:
                self.df.to_csv(self.output_file, index=False)
                logger.info(f"Successfully saved cleaned dataset to {self.output_file}")
            else:
                logger.warning("No data available to save. The DataFrame is empty or not initialized.")
        except Exception as e:
            logger.error(f"Failed to save cleaned data: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    cleaner = DataCleaner()
    cleaner.clean_data()
    cleaner.save_cleaned_data()
