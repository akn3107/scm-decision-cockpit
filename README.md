# Supply Chain Risk Cockpit MVP
Deterministic, Excel-based Control Tower for Supply Chain Decision Making.

## Quick Start
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Generate Input Template**:
   ```bash
   python make_template.py
   ```
   This creates `control_tower_input.xlsx` with sample data.
3. **Run the Cockpit**:
   ```bash
   streamlit run app.py
   ```
4. **Upload Data**:
   - In the browser window, upload `control_tower_input.xlsx`.

## Components
- `make_template.py`: Generates the strict Excel schema.
- `validator.py`: Enforces data integrity rules (negative values, date alignment).
- `kpi_engine.py`: Core logic for NAI, POH, Fill Rate, and Scenario math.
- `app.py`: Streamlit frontend for visualization and "What-If" analysis.

## Scenarios
Use the sidebar to adjust:
- **Demand Uplift**: Stress-test inventory against higher demand.
- **Supply Delay**: Simulate late arrivals from plants/suppliers.
