#!/bin/bash
# Step 2: Launch Dashboard
# This script launches the Streamlit dashboard to visualize the results.

echo "========================================"
echo "   STEP 2: LAUNCHING DASHBOARD          "
echo "========================================"

if [ ! -f "final_report.json" ]; then
    echo "ERROR: 'final_report.json' not found."
    echo "Please run './1_generate_data.sh' first."
    exit 1
fi

echo "[*] Starting Streamlit Server..."
echo "    The dashboard should open in your browser automatically."
echo "    If not, click the URL shown below."
echo "----------------------------------------"

streamlit run dashboard.py
