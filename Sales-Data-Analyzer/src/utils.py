import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import logging
from config import RAW_DATA_FILE, NUM_ROWS_TO_GENERATE

logger = logging.getLogger(__name__)

# Realistic categories and their respective products with base prices
PRODUCT_CATALOG = {
    "Electronics": [
        ("Laptop", 800.0, 1500.0),
        ("Smartphone", 500.0, 1000.0),
        ("Headphones", 50.0, 300.0),
        ("Smartwatch", 150.0, 400.0),
        ("Tablet", 300.0, 700.0)
    ],
    "Clothing": [
        ("T-Shirt", 15.0, 35.0),
        ("Jeans", 40.0, 90.0),
        ("Winter Jacket", 80.0, 200.0),
        ("Sneakers", 60.0, 150.0),
        ("Sweater", 30.0, 80.0)
    ],
    "Home & Garden": [
        ("Blender", 40.0, 100.0),
        ("Coffee Maker", 50.0, 250.0),
        ("Vacuum Cleaner", 100.0, 400.0),
        ("Bed Sheets", 25.0, 80.0),
        ("Desk Lamp", 20.0, 60.0)
    ],
    "Sports": [
        ("Yoga Mat", 15.0, 40.0),
        ("Dumbbells Set", 50.0, 150.0),
        ("Tennis Racket", 60.0, 200.0),
        ("Football", 15.0, 35.0),
        ("Running Shoes", 70.0, 160.0)
    ],
    "Toys": [
        ("Action Figure", 10.0, 30.0),
        ("Board Game", 20.0, 60.0),
        ("Lego Set", 30.0, 120.0),
        ("RC Car", 40.0, 100.0),
        ("Puzzle", 10.0, 25.0)
    ]
}

REGIONS = ["North America", "Europe", "Asia", "South America", "Oceania"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "Bank Transfer"]

def generate_sample_data(num_rows: int = NUM_ROWS_TO_GENERATE, file_path=RAW_DATA_FILE) -> None:
    """
    Generates a realistic sample dataset for sales and saves it to a CSV file.
    """
    logger.info(f"Generating {num_rows} rows of highly realistic sales data...")

    # Data lists
    start_date = datetime.now() - timedelta(days=5 * 365) # 5 years ago
    dates = [start_date + timedelta(days=random.randint(0, 5 * 365)) for _ in range(num_rows)]
    
    # Flatten catalog for easy random choice
    flat_catalog = []
    for category, products in PRODUCT_CATALOG.items():
        for product_name, min_price, max_price in products:
            flat_catalog.append((category, product_name, min_price, max_price))

    # Generate random indices for products
    product_indices = np.random.randint(0, len(flat_catalog), num_rows)
    
    categories = []
    products = []
    unit_prices = []
    
    for idx in product_indices:
        cat, prod, min_p, max_p = flat_catalog[idx]
        categories.append(cat)
        products.append(prod)
        # Random price within realistic bounds for that specific product
        unit_prices.append(round(random.uniform(min_p, max_p), 2))
    
    data = {
        "Invoice_ID": [f"INV-{200000 + i}" for i in range(1, num_rows + 1)],
        "Date": dates,
        "Product": products,
        "Category": categories,
        "Customer": [f"Customer_{random.randint(1000, 9999)}" for _ in range(num_rows)],
        "Region": np.random.choice(REGIONS, num_rows),
        "Salesperson": [f"Rep_{random.randint(10, 99)}" for _ in range(num_rows)],
        "Units_Sold": np.random.randint(1, 15, num_rows), # Realistic small retail quantities
        "Unit_Price": unit_prices,
        "Discount": np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], num_rows, p=[0.5, 0.2, 0.15, 0.1, 0.05]),
        "Payment_Method": np.random.choice(PAYMENT_METHODS, num_rows),
    }

    df = pd.DataFrame(data)

    # Calculate dependent columns correctly
    df["Sales"] = (df["Units_Sold"] * df["Unit_Price"] * (1 - df["Discount"])).round(2)
    
    # Realistic cost (assume a 30-50% profit margin depending on category)
    # So Cost is 50-70% of the ORIGINAL price (before discount)
    cost_percentage = np.random.uniform(0.5, 0.7, num_rows)
    df["Cost"] = (df["Units_Sold"] * df["Unit_Price"] * cost_percentage).round(2)
    df["Profit"] = (df["Sales"] - df["Cost"]).round(2)

    # Extract time-based features
    df["Month"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.quarter
    df["Year"] = df["Date"].dt.year
    
    # Sort by date to make it realistic
    df = df.sort_values("Date").reset_index(drop=True)

    # Save to CSV
    df.to_csv(file_path, index=False)
    logger.info(f"Successfully saved realistic dataset to {file_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_sample_data()
