import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import datetime

def compute_kpis(
    inv: pd.DataFrame, 
    demand: pd.DataFrame, 
    supply: pd.DataFrame, 
    horizon_weeks: int = 8,
    demand_uplift_pct: float = 0.0,
    supply_delay_weeks: int = 0
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes deterministic supply chain KPIs.
    
    Args:
        inv: Inventory snapshot (sku, location, on_hand_qty, etc.)
        demand: Weekly demand (week_start, sku, location, forecast_qty)
        supply: Weekly supply (week_start, sku, location, supply_qty)
        horizon_weeks: Number of weeks to project
        demand_uplift_pct: Scenario lever (e.g. 0.10 for 10% uplift)
        supply_delay_weeks: Scenario lever (shift supply by N weeks)
        
    Returns:
        (summary_df, detail_df)
    """
    
    # ----------------------------------------------------
    # 1. Pre-process & Scenario Application
    # ----------------------------------------------------
    inv = inv.copy()
    d_df = demand.copy()
    s_df = supply.copy()
    
    # Ensure minimal schema for empty dfs to avoid key errors later
    if d_df.empty: 
        d_df = pd.DataFrame(columns=["week_start", "sku", "location", "forecast_qty"])
    if s_df.empty:
        s_df = pd.DataFrame(columns=["week_start", "sku", "location", "supply_qty"])
    if inv.empty:
        inv = pd.DataFrame(columns=["as_of_date", "sku", "location", "on_hand_qty", "safety_stock_qty"])

    # Ensure dates
    for df, col in [(inv, "as_of_date"), (d_df, "week_start"), (s_df, "week_start")]:
        # Safety for columns existing now
        if col not in df.columns: df[col] = []
        df[col] = pd.to_datetime(df[col]).dt.date

    # Numeric conversion
    for df, col in [(d_df, "forecast_qty"), (s_df, "supply_qty"), (inv, "on_hand_qty"), (inv, "safety_stock_qty")]:
        if col not in df.columns: df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Scenarios
    if demand_uplift_pct != 0:
        d_df["forecast_qty"] *= (1.0 + demand_uplift_pct)
        
    if supply_delay_weeks > 0:
        # Add weeks to week_start
        s_df["week_start"] = pd.to_datetime(s_df["week_start"]) + pd.to_timedelta(7 * supply_delay_weeks, unit="D")
        s_df["week_start"] = s_df["week_start"].dt.date

    # ----------------------------------------------------
    # 2. Build Grid (SKU-Location-Week)
    # ----------------------------------------------------
    # Determine start week
    starts = []
    if not d_df.empty: starts.append(d_df["week_start"].min())
    if not s_df.empty: starts.append(s_df["week_start"].min())
    
    if starts:
        start_week = min(starts)
    else:
        start_week = datetime.date.today()
    
    # Normalize to Monday (0)
    # If using ISO weeks, we want the Monday of that week.
    start_week = start_week - datetime.timedelta(days=start_week.weekday())

    weeks = [start_week + datetime.timedelta(days=7*i) for i in range(horizon_weeks)]
    weeks_df = pd.DataFrame({"week_start": weeks})
    
    keys = inv[["sku", "location"]].drop_duplicates()
    
    # Cartesian product: Keys x Weeks
    grid = keys.assign(_k=1).merge(weeks_df.assign(_k=1), on="_k").drop(columns="_k")
    
    # Aggregate demand/supply to SKU-Loc-Week level
    d_agg = d_df.groupby(["sku", "location", "week_start"], as_index=False)["forecast_qty"].sum()
    s_agg = s_df.groupby(["sku", "location", "week_start"], as_index=False)["supply_qty"].sum()
    
    # Merge into grid
    detail = grid.merge(d_agg, on=["sku", "location", "week_start"], how="left") \
                 .merge(s_agg, on=["sku", "location", "week_start"], how="left") \
                 .fillna({"forecast_qty": 0, "supply_qty": 0})
                 
    # Merge initial inventory
    inv_agg = inv.groupby(["sku", "location"], as_index=False)[["on_hand_qty", "safety_stock_qty"]].sum()
    detail = detail.merge(inv_agg, on=["sku", "location"], how="left").fillna(0)
    
    # ----------------------------------------------------
    # 3. Recursive Calculation (NAI, POH, etc.)
    # ----------------------------------------------------
    detail = detail.sort_values(["sku", "location", "week_start"])
    
    nai_list = []
    poh_list = []
    served_list = []
    unmet_list = []
    
    # Iterate by group is usually fast enough for MVP scale
    for _, g in detail.groupby(["sku", "location"]):
        # Initial state
        oh = g["on_hand_qty"].iloc[0]
        nai_prev = oh
        
        for idx, row in g.iterrows():
            d_t = row["forecast_qty"]
            s_t = row["supply_qty"]
            
            # Available to serve this week = what we had left + what just arrived
            avail = max(0, nai_prev + s_t)
            
            served = min(d_t, avail)
            unmet = d_t - served
            
            # Net Available Inventory (Carry over) -> Math: OH + CumS - CumD
            # Iterative equivalent: NAI_t = NAI_{t-1} + S_t - D_t
            # Note: NAI can be negative (backlog hole)
            nai = nai_prev + s_t - d_t
            
            # Projected On Hand (Physical stock) -> cannot be negative
            poh = max(0, nai)
            
            nai_list.append(nai)
            poh_list.append(poh)
            served_list.append(served)
            unmet_list.append(unmet)
            
            nai_prev = nai

    detail["NAI"] = nai_list
    detail["POH"] = poh_list
    detail["served_qty"] = served_list
    detail["unmet_qty"] = unmet_list
    
    # ----------------------------------------------------
    # 4. Summary Stats
    # ----------------------------------------------------
    # Safety stock breach column for calculation
    detail["ss_breach"] = (detail["POH"] < detail["safety_stock_qty"])
    detail["stockout"] = (detail["NAI"] < 0)

    summary = detail.groupby(["sku", "location"], as_index=False).agg(
        total_demand=("forecast_qty", "sum"),
        total_served=("served_qty", "sum"),
        total_unmet=("unmet_qty", "sum"),
        min_nai=("NAI", "min"),
        min_poh=("POH", "min"),
        safety_stock_qty=("safety_stock_qty", "max"),
        on_hand_qty=("on_hand_qty", "max")
    )
    
    summary["fill_rate"] = np.where(
        summary["total_demand"] > 0, 
        summary["total_served"] / summary["total_demand"], 
        1.0
    )
    
    summary["stockout_flag"] = (summary["min_nai"] < 0).astype(int)
    
    # First Stockout Week
    stockouts = detail[detail["stockout"]].groupby(["sku", "location"], as_index=False)["week_start"].min()
    stockouts.rename(columns={"week_start": "first_stockout_week"}, inplace=True)
    summary = summary.merge(stockouts, on=["sku", "location"], how="left")
    
    # Safety Breach Logic
    # We check if min(POH) < safety_stock. 
    # (Checking against max safety_stock is a simplification if SS varies by time, but demanded by MVP spec)
    summary["safety_breach_flag"] = (summary["min_poh"] < summary["safety_stock_qty"]).astype(int)
    
    breaches = detail[detail["ss_breach"]].groupby(["sku", "location"], as_index=False)["week_start"].min()
    breaches.rename(columns={"week_start": "first_safety_breach_week"}, inplace=True)
    summary = summary.merge(breaches, on=["sku", "location"], how="left")

    return summary, detail
