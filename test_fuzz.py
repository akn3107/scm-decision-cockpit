import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st
from kpi_engine import compute_kpis
import datetime

# Strategies for generating random data
@st.composite
def supply_chain_data(draw):
    # Generate common SKUs/Locations
    skus = draw(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3))
    locs = draw(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=2))
    
    # Inventory
    inv_data = []
    for s in skus:
        for l in locs:
            inv_data.append({
                "as_of_date": datetime.date(2026, 1, 1),
                "sku": s,
                "location": l,
                "on_hand_qty": draw(st.integers(min_value=0, max_value=1000000)),
                "safety_stock_qty": draw(st.integers(min_value=0, max_value=100000))
            })
    inv = pd.DataFrame(inv_data)
    
    # Demand
    d_rows = []
    num_weeks = draw(st.integers(min_value=1, max_value=10))
    start_date = datetime.date(2026, 1, 19)
    for w in range(num_weeks):
        wk = start_date + datetime.timedelta(days=7*w)
        for s in skus:
            for l in locs:
                if draw(st.booleans()): # Random sparseness
                    d_rows.append({
                        "week_start": wk,
                        "sku": s,
                        "location": l,
                        "forecast_qty": draw(st.floats(min_value=0, max_value=50000))
                    })
    dem = pd.DataFrame(d_rows)
    
    # Supply
    s_rows = []
    for w in range(num_weeks):
        wk = start_date + datetime.timedelta(days=7*w)
        for s in skus:
            for l in locs:
                if draw(st.booleans()):
                    s_rows.append({
                        "week_start": wk,
                        "sku": s,
                        "location": l,
                        "supply_qty": draw(st.floats(min_value=0, max_value=50000))
                    })
    sup = pd.DataFrame(s_rows)
    
    return inv, dem, sup

@settings(max_examples=50, deadline=None)
@given(supply_chain_data())
def test_fuzz_kpi_engine_crash(data):
    """
    Aggressively fuzz the engine with random valid inputs.
    We just want to ensure it doesn't CRASH (raise exceptions).
    Logic correctness is covered by unit tests.
    """
    inv, dem, sup = data
    
    # Also fuzz scenario params
    uplift = 0.1 # Simplification: fix scenario to keep test fast
    delay = 1
    
    try:
        summ, det = compute_kpis(inv, dem, sup, horizon_weeks=4, demand_uplift_pct=uplift, supply_delay_weeks=delay)
    except Exception as e:
        pytest.fail(f"KPI Engine crashed on fuzz input: {str(e)}")

    # Basic invariants
    if not summ.empty:
        assert (summ["fill_rate"] <= 1.000001).all() # Float tolerance
        assert (summ["on_hand_qty"] >= 0).all()
