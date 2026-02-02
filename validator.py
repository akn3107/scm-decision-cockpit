import pandas as pd
from typing import Dict, List, Tuple
import datetime

REQUIRED_SHEETS = ["Inventory", "Demand_Plan", "Supply_Plan"]

REQUIRED_COLS = {
    "Inventory": ["as_of_date", "sku", "location", "on_hand_qty"],
    "Demand_Plan": ["week_start", "sku", "location", "forecast_qty"],
    "Supply_Plan": ["week_start", "sku", "location", "supply_qty"],
}

def validate_data(dfs: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
    """
    Validates the input DataFrames against strict schema and business rules.
    
    Returns:
        (is_valid, list_of_error_messages)
    """
    errors = []
    
    # 1. Check Required Sheets
    for sh in REQUIRED_SHEETS:
        if sh not in dfs:
            errors.append(f"Missing required sheet: {sh}")
            continue
            
        df = dfs[sh]
        
        # 2. Check Required Columns
        if df.empty:
             errors.append(f"Sheet {sh} is empty.")
             continue

        cols = set(df.columns.astype(str))
        missing_cols = [c for c in REQUIRED_COLS[sh] if c not in cols]
        if missing_cols:
            errors.append(f"Sheet {sh} missing columns: {missing_cols}")
    
    if errors:
        return False, errors

    # 3. Type & Value Checks
    
    # Inventory
    inv = dfs["Inventory"]
    if not inv.empty:
        # Check qty non-negative
        for c in ["on_hand_qty", "safety_stock_qty"]:
            if c in inv.columns:
                 if pd.to_numeric(inv[c], errors='coerce').fillna(0).min() < 0:
                     errors.append(f"Inventory sheet contains negative values in {c}")

    # Demand Plan
    dem = dfs["Demand_Plan"]
    if not dem.empty:
        # Check week_start is Monday
        if "week_start" in dem.columns:
            # Ensure datetime
            try:
                dates = pd.to_datetime(dem["week_start"], errors='coerce')
                if dates.isna().any():
                    errors.append("Demand_Plan: Invalid dates in week_start")
                else:
                    # Check for Monday (weekday 0)
                    not_monday = dates[dates.dt.weekday != 0]
                    if not not_monday.empty:
                        errors.append(f"Demand_Plan: week_start must be Mondays. Found {len(not_monday)} invalid rows.")
            except Exception as e:
                 errors.append(f"Demand_Plan: Date parsing error: {str(e)}")
        
        # Check forecast non-negative
        if "forecast_qty" in dem.columns:
             if pd.to_numeric(dem["forecast_qty"], errors='coerce').fillna(0).min() < 0:
                 errors.append("Demand_Plan: forecast_qty contains negative values")

    # Supply Plan
    sup = dfs["Supply_Plan"]
    if not sup.empty:
        # Check week_start is Monday
        if "week_start" in sup.columns:
            try:
                dates = pd.to_datetime(sup["week_start"], errors='coerce')
                if dates.isna().any():
                     errors.append("Supply_Plan: Invalid dates in week_start")
                else:
                    not_monday = dates[dates.dt.weekday != 0]
                    if not not_monday.empty:
                        errors.append(f"Supply_Plan: week_start must be Mondays. Found {len(not_monday)} invalid rows.")
            except:
                pass

        if "supply_qty" in sup.columns:
             if pd.to_numeric(sup["supply_qty"], errors='coerce').fillna(0).min() < 0:
                 errors.append("Supply_Plan: supply_qty contains negative values")

    return (len(errors) == 0), errors
