import pytest
import pandas as pd
from datetime import date, timedelta
from validator import validate_data

def test_valid_data():
    dfs = {
        "Inventory": pd.DataFrame({
            "as_of_date": [date(2026,1,1)],
            "sku": ["A"],
            "location": ["L"],
            "on_hand_qty": [100]
        }),
        "Demand_Plan": pd.DataFrame({
            "week_start": [date(2026,1,19)], # Monday
            "sku": ["A"],
            "location": ["L"],
            "forecast_qty": [10]
        }),
        "Supply_Plan": pd.DataFrame({
            "week_start": [date(2026,1,19)], # Monday
            "sku": ["A"],
            "location": ["L"],
            "supply_qty": [50]
        })
    }
    ok, errs = validate_data(dfs)
    assert ok is True
    assert len(errs) == 0

def test_missing_sheet():
    dfs = {"Inventory": pd.DataFrame()}
    ok, errs = validate_data(dfs)
    assert ok is False
    assert any("Missing required sheet" in e for e in errs)

def test_negative_qty():
    dfs = {
        "Inventory": pd.DataFrame({
            "as_of_date": [date(2026,1,1)],
            "sku": ["A"],
            "location": ["L"],
            "on_hand_qty": [-10] # Bad
        }),
        "Demand_Plan": pd.DataFrame({
            "week_start": [date(2026,1,19)], 
            "sku": ["A"], "location": ["L"], "forecast_qty": [10]
        }),
        "Supply_Plan": pd.DataFrame({
            "week_start": [date(2026,1,19)], 
            "sku": ["A"], "location": ["L"], "supply_qty": [10]
        })
    }
    ok, errs = validate_data(dfs)
    assert ok is False
    assert any("Inventory sheet contains negative values" in e for e in errs)

def test_non_monday_dates():
    dfs = {
        "Inventory": pd.DataFrame({
            "as_of_date": [date(2026,1,1)], "sku": ["A"], "location": ["L"], "on_hand_qty": [100]
        }),
        "Demand_Plan": pd.DataFrame({
            "week_start": [date(2026,1,20)], # Tuesday, Invalid
            "sku": ["A"], "location": ["L"], "forecast_qty": [10]
        }),
        "Supply_Plan": pd.DataFrame({
            "week_start": [date(2026,1,19)], 
            "sku": ["A"], "location": ["L"], "supply_qty": [10]
        })
    }
    ok, errs = validate_data(dfs)
    assert ok is False
    assert any("week_start must be Mondays" in e for e in errs)
