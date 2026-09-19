import pandas as pd
import re
from typing import Tuple, Dict, Any, List

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names to lowercase snake_case for Jinja templates."""
    def clean_name(name):
        name = str(name).strip().lower()
        name = re.sub(r'[^a-z0-9]+', '_', name)
        return name.strip('_')
    
    df.columns = [clean_name(c) for c in df.columns]
    
    # Map common variations
    mapping = {
        'id': 'employee_id',
        'emp_id': 'employee_id',
        'name': 'full_name',
        'employee_name': 'full_name'
    }
    df = df.rename(columns=mapping)
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Removes empty rows and cleans whitespace."""
    # Replace nan with empty string
    df = df.fillna("")
    
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].astype(str).str.strip()
        
    # Drop rows that are completely empty
    df = df.replace("", pd.NA).dropna(how='all').fillna("")
    
    # Drop exact duplicates
    df = df.drop_duplicates()
    
    return df
