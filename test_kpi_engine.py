import pytest
import pandas as pd
from datetime import date
from kpi_engine import compute_kpis

def test_basic_kpi():
    # Setup: 1 SKU, 1 Location, 2 Weeks
    # Week 1: D=10, S=0. Intitial OH=5. -> Unmet=5, NAI=-5
    # Week 2: D=10, S=20. Prev NAI=-5. Avail=15. Served=10. NAI=5.
    
    inv = pd.DataFrame([{
        "as_of_date": date(2026,1,1), "sku": "A", "location": "L", 
        "on_hand_qty": 5, "safety_stock_qty": 0
    }])
    
    w1 = date(2026,1,19)
    w2 = date(2026,1,26)
    
    dem = pd.DataFrame([
        {"week_start": w1, "sku": "A", "location": "L", "forecast_qty": 10},
        {"week_start": w2, "sku": "A", "location": "L", "forecast_qty": 10},
    ])
    
    sup = pd.DataFrame([
        {"week_start": w2, "sku": "A", "location": "L", "supply_qty": 20}
    ])
    
    summ, det = compute_kpis(inv, dem, sup, horizon_weeks=2)
    
    # Check Detail
    # Sort just in case
    det = det.sort_values("week_start")
    
    # Week 1
    row1 = det.iloc[0]
    assert row1["week_start"] == w1
    assert row1["forecast_qty"] == 10
    assert row1["served_qty"] == 5   # OH=5
    assert row1["unmet_qty"] == 5
    assert row1["NAI"] == -5
    
    # Week 2
    row2 = det.iloc[1]
    assert row2["week_start"] == w2
    assert row2["supply_qty"] == 20
    assert row2["served_qty"] == 10
    # NAI = -5 + 20 - 10 = 5
    assert row2["NAI"] == 5
    
    # Check Summary
    s_row = summ.iloc[0]
    assert s_row["total_demand"] == 20
    assert s_row["total_served"] == 15
    assert s_row["stockout_flag"] == 1
    assert s_row["first_stockout_week"] == w1

def test_scenario_uplift():
    # Demand = 100. Uplift 10% -> 110.
    inv = pd.DataFrame([{"as_of_date": date(2026,1,1), "sku": "A", "location": "L", "on_hand_qty": 1000, "safety_stock_qty": 0}])
    dem = pd.DataFrame([{"week_start": date(2026,1,19), "sku": "A", "location": "L", "forecast_qty": 100}])
    sup = pd.DataFrame([])
    
    summ, det = compute_kpis(inv, dem, sup, demand_uplift_pct=0.10)
    assert det.iloc[0]["forecast_qty"] == pytest.approx(110.0)

def test_scenario_delay():
    # Supply in W1. Delay 1 week -> Supply in W2.
    w1 = date(2026,1,19)
    w2 = date(2026,1,26)
    inv = pd.DataFrame([{"as_of_date": date(2026,1,1), "sku": "A", "location": "L", "on_hand_qty": 0, "safety_stock_qty": 0}])
    # Anchor demand at w1 so grid starts there, even if supply shifts to w2
    dem = pd.DataFrame([{"week_start": w1, "sku": "A", "location": "L", "forecast_qty": 0}])
    sup = pd.DataFrame([{"week_start": w1, "sku": "A", "location": "L", "supply_qty": 50}])
    
    summ, det = compute_kpis(inv, dem, sup, supply_delay_weeks=1, horizon_weeks=2)
    
    # Inspect detail
    det = det.set_index("week_start")
    
    # W1 should have 0 supply
    assert det.loc[w1]["supply_qty"] == 0
    # W2 should have 50 supply
    assert det.loc[w2]["supply_qty"] == 50
