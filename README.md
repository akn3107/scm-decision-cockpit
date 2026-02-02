# Supply Chain Decision Tool

A deterministic, Excel-driven supply chain risk analysis tool that helps you identify stockouts, excess inventory, and revenue at risk—without machine learning complexity.

![Supply Chain Insider](assets/header.jpg)

## 🎯 About

This tool empowers supply chain professionals to make data-driven decisions by:
- **Calculating KPIs**: Net Available Inventory (NAI), Projected On-Hand (POH), Fill Rate, Revenue at Risk
- **Identifying Risks**: Stockout flags, safety stock breaches, first-week-of-risk alerts
- **Scenario Analysis**: Test demand uplifts and supply delays to understand impact
- **Actionable Insights**: Prioritized recommendations (Expedite, Replenish, Promo)

**No machine learning. No black boxes. Just transparent, defensible math.**

## 🔒 Privacy & Data Security

**Your data never leaves your browser.** This tool:
- Processes all data **client-side** (in your browser or local environment)
- **Does not store, transmit, or log** any uploaded files
- **Does not require authentication** or user accounts
- Is fully open-source for transparency

Upload your data with confidence—it stays 100% private.

## ✨ Features

### Core Capabilities
- **Excel Template-Based**: Strict schema ensures predictable inputs/outputs
- **Deterministic Logic**: Transparent calculations you can audit and trust
- **Scenario Modeling**: 
  - Demand Uplift (0-50%)
  - Supply Delay (0-8 weeks)
  - Custom planning horizons (4-16 weeks)
- **Executive Dashboard**: Revenue at Risk, Stockout Count, Fill Rate, Safety Breaches
- **Drilldown Analysis**: SKU-Location level weekly projections with charts
- **Export to PowerPoint**: Download dashboard results as a presentation

### Built For
- **Pharma Supply Chains**: Sample data includes pharma SKUs (Paracetamol, Amoxicillin, etc.)
- **Multi-SKU, Multi-Location**: Handles complex distribution networks
- **Weekly Bucketing**: Aligns with typical S&OP cycles

## 🚀 How to Use

### 1. Download the Template
Visit the [live tool](https://scm-decision-tool.streamlit.app) and click **"Download Excel Template"** on the Home page.

### 2. Fill Your Data
The template includes these sheets:
- **Inventory**: Current stock snapshot (on-hand, safety stock, QA hold)
- **Demand_Plan**: Weekly forecast by SKU/Location
- **Supply_Plan**: Incoming supply/production schedule
- **Master_Data** (optional): Unit revenue, COGS for economic calculations
- **Help**: Column definitions and tips

**Important**: 
- Dates must be in `YYYY-MM-DD` format
- `week_start` must be Mondays
- Do not rename sheets or columns

### 3. Upload & Analyze
- Go to the **"Tool"** page
- Upload your filled Excel file
- Adjust scenario parameters in the sidebar (optional)
- View KPIs, prioritized actions, and drilldown charts

### 4. Export Results
Click **"Download as PowerPoint"** to save your dashboard for presentations.

## 📊 Use Cases

### Scenario 1: Stockout Prevention
**Problem**: Amoxicillin has only 20K units on-hand but 40K weekly demand.  
**Tool Output**: Flags stockout in Week 1, calculates Revenue at Risk, recommends "EXPEDITE".

### Scenario 2: Excess Inventory
**Problem**: Ibuprofen has 800K units but only 20K weekly demand.  
**Tool Output**: Identifies excess, recommends "PROMO / REDISTRIBUTE".

### Scenario 3: What-If Analysis
**Question**: What if demand increases 20% due to flu season?  
**Tool Action**: Adjust "Demand Uplift" slider, see updated stockout risks instantly.

## 🛠️ Tech Stack

- **Python 3.13+**
- **Streamlit**: Web UI framework
- **Pandas**: Data processing
- **OpenPyXL**: Excel file handling
- **python-pptx**: PowerPoint generation
- **Pytest + Hypothesis**: Unit and fuzz testing

## 📦 Deployment

### Option 1: Streamlit Cloud (Recommended)
1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy from your GitHub repo
4. Set `Main file path` to `app.py`

### Option 2: Local Development
```bash
# Clone repository
git clone https://github.com/akn3107/scm-decision-cockpit.git
cd scm-decision-cockpit

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Generate sample template (optional)
python make_template.py

# Run application
streamlit run app.py
```

### Option 3: Docker
```bash
docker build -t scm-tool .
docker run -p 8501:8501 scm-tool
```
Access at `http://localhost:8501`

## 🧪 Testing

```bash
# Run unit tests
pytest test_validator.py test_kpi_engine.py

# Run fuzz tests (property-based testing)
pytest test_fuzz.py
```

## 📁 Project Structure

```
scm-decision-cockpit/
├── app.py                              # Main Streamlit application
├── kpi_engine.py                       # Core KPI calculation logic
├── validator.py                        # Excel schema validation
├── make_template.py                    # Template generator
├── control_tower_input_with_help.xlsx  # Sample template
├── requirements.txt                    # Python dependencies
├── test_*.py                           # Unit and fuzz tests
├── assets/                             # Images (header)
└── README.md                           # This file
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - feel free to use this tool for commercial or personal projects.

## 👤 Author

**Ankit Nanda**  
Supply Chain Professional | Data-Driven Decision Making

- [Substack: Supply Chain Insider](https://substack.com/@ankitnanda)
- [LinkedIn](https://www.linkedin.com/in/ankitnanda/)

---

