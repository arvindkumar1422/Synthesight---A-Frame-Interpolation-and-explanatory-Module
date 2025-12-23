#!/bin/bash
# Step 1: Generate Data
# This script cleans up previous runs and generates new interpolation data.

echo "========================================"
echo "   STEP 1: GENERATING RESEARCH DATA     "
echo "========================================"

# 1. Clean up old data
echo "[*] Cleaning up old files..."
rm -rf debug_frames
rm -f restored_output.mp4 final_report.json smooth_synthetic.mp4 choppy_input.mp4
mkdir -p debug_frames

# 2. Generate Synthetic Data
echo "[*] Generating Synthetic Smooth Video..."
python src/utils/video_degrader.py generate --output smooth_synthetic.mp4

echo "[*] Degrading Video (Simulating Lag)..."
# Degrade by factor of 6 (30fps -> 5fps)
python src/utils/video_degrader.py degrade smooth_synthetic.mp4 --output choppy_input.mp4 --factor 6

# 3. Run the pipeline
echo "[*] Running Interpolation Pipeline..."
echo "    Input:  choppy_input.mp4 (5 FPS)"
echo "    Output: restored_output.mp4 (10 FPS)"
echo "    Report: final_report.json"
echo "----------------------------------------"

python main.py choppy_input.mp4 --output restored_output.mp4 --report final_report.json

# 4. Verify Output
if [ -f "restored_output.mp4" ] && [ -f "final_report.json" ]; then
    echo "----------------------------------------"
    echo "SUCCESS: Data generated successfully."
    echo "You can now run './2_launch_dashboard.sh' to view the results."
    echo "========================================"
else
    echo "----------------------------------------"
    echo "ERROR: Failed to generate output files."
    exit 1
fi
