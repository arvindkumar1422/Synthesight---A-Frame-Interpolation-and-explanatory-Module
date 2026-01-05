#!/bin/bash

# Exit on error
set -e

INPUT_VIDEO="my_video.mp4"
ENHANCED_2X="my_video_2x.mp4"
ENHANCED_4X="my_video_4x.mp4"

echo "========================================================"
echo "SyntheSight: Direct Enhancement (Original -> Super Smooth)"
echo "========================================================"

# Pass 1: 24 FPS -> 48 FPS
echo "[1/2] Enhancing 2x (Original -> 48 FPS)..."
python main.py "$INPUT_VIDEO" -o "$ENHANCED_2X" -r "report_enhance_2x.json"

# Pass 2: 48 FPS -> 96 FPS
echo "[2/2] Enhancing 4x (48 FPS -> 96 FPS)..."
python main.py "$ENHANCED_2X" -o "$ENHANCED_4X" -r "report_enhance_4x.json"

echo "========================================================"
echo "Enhancement Complete!"
echo "Original: $INPUT_VIDEO"
echo "2x Smooth: $ENHANCED_2X"
echo "4x Smooth: $ENHANCED_4X (Super Smooth!)"
echo "========================================================"

# Inspect results
python inspect_videos.py
