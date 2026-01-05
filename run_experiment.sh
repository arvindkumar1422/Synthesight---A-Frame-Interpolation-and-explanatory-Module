#!/bin/bash

# Exit on error
set -e

INPUT_VIDEO="my_video.mp4"
CHOPPY_VIDEO="my_choppy_video.mp4"
RESTORED_1="my_restored_pass1.mp4"
RESTORED_2="my_restored_final.mp4"

echo "========================================================"
echo "Running SyntheSight Experiment: Super-Smooth Restoration"
echo "========================================================"

# 1. Choppify (Original -> 10 FPS)
echo "[1/3] Choppifying original video to 10 FPS..."
python generate_choppy_video.py "$INPUT_VIDEO" -o "$CHOPPY_VIDEO" -f 10

# 2. Restore Pass 1 (10 FPS -> 20 FPS)
echo "[2/3] Running Restoration Pass 1 (10 -> 20 FPS)..."
python main.py "$CHOPPY_VIDEO" -o "$RESTORED_1" -r "report_pass1.json"

# 3. Restore Pass 2 (20 FPS -> 40 FPS)
echo "[3/3] Running Restoration Pass 2 (20 -> 40 FPS)..."
# We use the output of pass 1 as input here
python main.py "$RESTORED_1" -o "$RESTORED_2" -r "report_pass2.json"

# 4. Super-Smooth 2x (Original -> 2x)
echo "[4/6] Generating Super-Smooth 2x (Original -> 2x)..."
python main.py "$INPUT_VIDEO" -o "my_video_2x.mp4" -r "report_2x.json"

# 5. Super-Smooth 4x (2x -> 4x)
echo "[5/6] Generating Super-Smooth 4x (2x -> 4x)..."
python main.py "my_video_2x.mp4" -o "my_video_4x.mp4" -r "report_4x.json"

# 6. Generate Final Report
echo "[6/6] Injecting Video Gallery and Stats into Report..."
python inspect_videos.py --inject-report "report_pass2.html"

echo "========================================================"
echo "Experiment Complete!"
echo "Original: $INPUT_VIDEO"
echo "Choppy:   $CHOPPY_VIDEO (10 FPS)"
echo "Pass 1:   $RESTORED_1 (20 FPS)"
echo "Final:    $RESTORED_2 (40 FPS)"
echo "2x Smooth: my_video_2x.mp4"
echo "4x Smooth: my_video_4x.mp4"
echo "========================================================"
