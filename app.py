import streamlit as st
import pandas as pd
import numpy as np
import io
import validator
import kpi_engine
import os

# Page Config
st.set_page_config(page_title="Supply Chain Risk Cockpit", layout="wide", page_icon="✈️")

# ---------------------------------------------------------
# Styles
# ---------------------------------------------------------
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .main-header {
        text-align: center;
    }
    .social-link {
        text-decoration: none;
        color: #0072b1;
        font-weight: bold;
        margin-right: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
@st.cache_data
def load_excel(file_bytes):
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    dfs = {}
    for sh in xls.sheet_names:
        dfs[sh] = pd.read_excel(xls, sheet_name=sh)
    return dfs

def enrich_master(df, dfs):
    """Joins master data (unit_revenue, cogs, etc.)"""
    if "Master_Data" not in dfs:
        df["unit_revenue"] = 1.0
        df["unit_cogs"] = 0.5
        return df
    
    m = dfs["Master_Data"].copy()
    if "location" in m.columns:
        m = m.drop_duplicates(subset=["sku", "location"])
        df = df.merge(m[["sku", "location", "unit_revenue", "unit_cogs"]], on=["sku", "location"], how="left")
    else:
        m = m.drop_duplicates(subset=["sku"])
        df = df.merge(m[["sku", "unit_revenue", "unit_cogs"]], on=["sku"], how="left")
        
    df["unit_revenue"] = df["unit_revenue"].fillna(1.0)
    df["unit_cogs"] = df["unit_cogs"].fillna(0.5)
    return df

# ---------------------------------------------------------
# Views
# ---------------------------------------------------------

def show_landing_page():
    # Header Image
    if os.path.exists("assets/header.jpg"):
        st.image("assets/header.jpg", use_container_width=True)
    
    st.title("Supply Chain Decision Cockpit")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("How to Use")
        st.markdown("""
        1. **Download the Template**: Get the required Excel format below.
        2. **Fill Your Data**: Enter Inventory, Demand, and Supply data.
        3. **Upload**: Go to the 'Tool' page and upload your file.
        4. **Analyze**: View Risk calculations and actionable recommendations.
        """)
        
        # Download Button
        template_path = "control_tower_input_with_help.xlsx"
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                st.download_button(
                    label="📥 Download Excel Template",
                    data=f,
                    file_name="control_tower_input_with_help.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("Template file not found. Please run make_template.py")

        st.write("") # Spacer
        if st.button("🚀 Launch Tool", type="primary"):
            st.session_state.page = "Tool"
            st.rerun()

    with col2:
        st.subheader("Connect with Me")
        st.markdown("""
        Built by **Ankit Nanda**.
        
        - [Substack: Supply Chain Insider](https://substack.com/@ankitnanda)
        - [LinkedIn Profile](https://www.linkedin.com/in/ankitnanda/)
        """)

def show_cockpit():
    st.header("Risk Control Tower")
    
    # Sidebar scenarios
    demand_uplift = st.sidebar.slider("Demand Uplift (%)", 0, 50, 0, 5) / 100.0
    supply_delay = st.sidebar.slider("Supply Delay (Weeks)", 0, 8, 0, 1)
    horizon = st.sidebar.slider("Planning Horizon (Weeks)", 4, 16, 8, 1)

    uploaded_file = st.file_uploader("Upload 'control_tower_input_with_help.xlsx'", type=["xlsx"])
    
    if not uploaded_file:
        st.info("👆 Please upload the data file to proceed.")
        return

    # Data Processing
    try:
        file_bytes = uploaded_file.read()
        dfs = load_excel(file_bytes)
        
        ok, errors = validator.validate_data(dfs)
        if not ok:
            st.error("❌ Data Validation Failed")
            for e in errors:
                st.write(f"- {e}")
            st.stop()
            
        inv = dfs["Inventory"]
        demand = dfs["Demand_Plan"]
        supply = dfs["Supply_Plan"]
        
        with st.spinner("Computing Scenarios..."):
            summary, detail = kpi_engine.compute_kpis(
                inv, demand, supply, 
                horizon_weeks=horizon,
                demand_uplift_pct=demand_uplift,
                supply_delay_weeks=supply_delay
            )
            
        summary = enrich_master(summary, dfs)
        summary["revenue_at_risk"] = summary["total_unmet"] * summary["unit_revenue"]
        
        # Executive Metrics
        tot_rar = summary["revenue_at_risk"].sum()
        skus_stockout = summary["stockout_flag"].sum()
        avg_fill = summary["fill_rate"].mean()
        safety_breaches = summary["safety_breach_flag"].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Revenue at Risk", f"${tot_rar:,.0f}")
        c2.metric("⚠️ SKUs with Stockouts", int(skus_stockout))
        c3.metric("📉 Avg Fill Rate", f"{avg_fill*100:.1f}%")
        c4.metric("🛡️ Safety Breaches", int(safety_breaches))
        
        st.divider()
        
        # Actions
        st.subheader("🔥 Top Actions")
        def recommend(row):
            if row["stockout_flag"]: return "🟥 EXPEDITE"
            if row["safety_breach_flag"]: return "🟧 REPLENISH"
            if row["min_poh"] > row["safety_stock_qty"]*3 and row["min_poh"] > 10000: return "🟦 PROMO"
            return "✅ OK"
            
        actions = summary.copy()
        actions["Recommendation"] = actions.apply(recommend, axis=1)
        actions = actions.sort_values(["revenue_at_risk", "first_stockout_week"], ascending=[False, True])
        
        st.dataframe(
            actions[[
                "sku", "location", "Recommendation", 
                "revenue_at_risk", "fill_rate", 
                "first_stockout_week", "first_safety_breach_week"
            ]].style.format({
                "revenue_at_risk": "${:,.0f}",
                "fill_rate": "{:.1%}"
            }).applymap(lambda x: "color: red; font-weight: bold" if "EXPEDITE" in str(x) else ("color: orange; font-weight: bold" if "REPLENISH" in str(x) else ""), subset=["Recommendation"]),
            use_container_width=True
        )
        
        # Drilldown
        st.divider()
        st.subheader("🔍 Drilldown")
        sku = st.selectbox("Select SKU", summary["sku"].unique())
        loc = st.selectbox("Select Location", summary[summary["sku"]==sku]["location"].unique())
        
        drill = detail[(detail["sku"]==sku) & (detail["location"]==loc)].copy()
        st.line_chart(drill.set_index("week_start")[["on_hand_qty", "forecast_qty", "supply_qty"]])
        st.dataframe(drill[["week_start", "forecast_qty", "supply_qty", "NAI", "POH", "served_qty", "unmet_qty"]].style.format("{:,.0f}"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")

# ---------------------------------------------------------
# Main Navigation
# ---------------------------------------------------------
def main():
    if "page" not in st.session_state:
        st.session_state.page = "Home"

    st.sidebar.title("Navigation")
    
    # Callback to sync sidebar with session state
    def on_change():
        st.session_state.page = st.session_state.nav_radio

    selection = st.sidebar.radio(
        "Go to", 
        ["Home", "Tool"], 
        key="nav_radio",
        index=0 if st.session_state.page == "Home" else 1,
        on_change=on_change
    )

    if st.session_state.page == "Home":
        show_landing_page()
    elif st.session_state.page == "Tool":
        show_cockpit()

if __name__ == "__main__":
    main()
