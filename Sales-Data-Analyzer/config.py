import os
from pathlib import Path

# Base directories — config.py lives in the project root
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CHARTS_DIR = BASE_DIR / "charts"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"

# Ensure directories exist
for directory in [DATA_DIR, REPORTS_DIR, CHARTS_DIR, LOGS_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Data files
RAW_DATA_FILE = DATA_DIR / "sales_data.csv"
CLEANED_DATA_FILE = DATA_DIR / "cleaned_sales_data.csv"
SUMMARY_DATA_FILE = DATA_DIR / "summary_statistics.csv"

# Model files
MODEL_FILE = MODELS_DIR / "sales_prediction_model.pkl"

# Log file
LOG_FILE = LOGS_DIR / "application.log"

# Settings for Data Generation
NUM_ROWS_TO_GENERATE = 50000

# Constants
CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Toys"]
REGIONS = ["North", "South", "East", "West", "Central"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Cash", "Bank Transfer"]
