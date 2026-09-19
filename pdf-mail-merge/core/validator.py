import pandas as pd
from typing import Tuple, Dict, Any, List

def validate_data(df: pd.DataFrame, required_fields: List[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Validates the dataset against required fields.
    Returns (valid_df, invalid_df, report).
    """
    if required_fields is None:
        required_fields = ['employee_id', 'full_name']
        
    report = {
        "total_records": len(df),
        "valid_records": 0,
        "invalid_records": 0,
        "duplicate_ids": 0,
        "missing_fields": {}
    }
    
    if df.empty:
        return df, pd.DataFrame(columns=df.columns), report
        
    # Ensure required columns exist, if not add them as empty so we can flag them
    for req in required_fields:
        if req not in df.columns:
            df[req] = ""
            
    # Check duplicates on employee_id if it exists
    if 'employee_id' in df.columns:
        dupes = df.duplicated(subset=['employee_id'], keep=False)
        report['duplicate_ids'] = dupes.sum()
        
    # Validate each row
    valid_mask = pd.Series(True, index=df.index)
    
    for req in required_fields:
        # Field is invalid if empty or NA
        is_missing = df[req].replace("", pd.NA).isna()
        missing_count = is_missing.sum()
        if missing_count > 0:
            report['missing_fields'][req] = int(missing_count)
            valid_mask = valid_mask & ~is_missing
            
    valid_df = df[valid_mask].copy()
    invalid_df = df[~valid_mask].copy()
    
    report['valid_records'] = len(valid_df)
    report['invalid_records'] = len(invalid_df)
    
    return valid_df, invalid_df, report
