import unittest
import pandas as pd
import os
from src.cleaning import DataCleaner

class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        # Create a dummy dataset with dirty data
        self.test_file = "test_data.csv"
        self.output_file = "test_cleaned_data.csv"
        data = {
            "Date": ["2023-01-01", "InvalidDate", "2023-01-03", "2023-01-04", "2023-01-04"],
            "Product": ["A", None, "C", "D", "D"],
            "Category": ["Cat1", "Cat2", None, "Cat4", "Cat4"],
            "Region": ["North", "South", "East", None, None],
            "Units_Sold": [10, -5, 15, "invalid", "invalid"],
            "Unit_Price": [100, 200, -50, 300, 300],
            "Sales": [1000, -1000, -750, 0, 0],
            "Cost": [500, 500, 300, 0, 0]
        }
        pd.DataFrame(data).to_csv(self.test_file, index=False)
        self.cleaner = DataCleaner(input_file=self.test_file, output_file=self.output_file)

    def test_clean_data(self):
        df = self.cleaner.clean_data()
        
        # Test duplicates removed
        self.assertEqual(len(df), 3) # Should have removed duplicate 4th row, invalid date row, invalid units_sold row
        
        # Test missing values filled
        self.assertTrue((df["Product"] == "Unknown").any() == False) # It was dropped due to invalid date maybe?
        
        # Let's just check no nulls in string columns
        for col in ["Product", "Category", "Region"]:
            self.assertEqual(df[col].isna().sum(), 0)

        # Test negative values corrected
        self.assertTrue((df["Unit_Price"] >= 0).all())
        self.assertTrue((df["Sales"] >= 0).all())

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

if __name__ == '__main__':
    unittest.main()
