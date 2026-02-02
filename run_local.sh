#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt

if [ ! -f "control_tower_input.xlsx" ]; then
    echo "Generating template..."
    python make_template.py
fi

echo "Starting App..."
streamlit run app.py
