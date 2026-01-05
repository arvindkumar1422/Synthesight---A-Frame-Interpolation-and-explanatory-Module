import cv2
import argparse
import sys
import os

def create_choppy_video(input_path, output_path, target_fps=10):
    """
    Creates a choppy version of the input video by dropping frames to match target_fps.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video '{input_path}'.")
        return

    original_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Input Video: {input_path}")
    print(f"Original FPS: {original_fps}")
    print(f"Target FPS: {target_fps}")
    
    if target_fps >= original_fps:
        print("Warning: Target FPS is higher than or equal to original FPS. Video might not look choppy.")

    # Calculate step size to skip frames
    # We want to keep 1 frame every (original_fps / target_fps) frames
    step = original_fps / target_fps
    
    # Use avc1 for better macOS compatibility
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_path, fourcc, target_fps, (width, height))
    
    frame_idx = 0
    kept_frames = 0
    
    print("Processing...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Logic to decide whether to keep this frame
        # We keep the frame if it's the closest integer frame to our target timeline
        # Simple approach: keep frame if index is a multiple of step (roughly)
        
        # Better approach: Accumulator
        # But simple modulo on integer index is easiest for fixed step if step is integer.
        # If step is float (e.g. 30 -> 10, step=3.0), index % 3 == 0.
        
        if frame_idx % int(step) == 0:
            out.write(frame)
            kept_frames += 1
            
        frame_idx += 1
        
        if frame_idx % 100 == 0:
            sys.stdout.write(f"\rProcessed {frame_idx}/{total_frames} frames")
            sys.stdout.flush()

    print(f"\nDone! Created {output_path}")
    print(f"Kept {kept_frames} frames out of {total_frames}.")
    
    cap.release()
    out.release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reduce video framerate to create a 'choppy' effect.")
    parser.add_argument("input_video", help="Path to input video")
    parser.add_argument("-o", "--output", default="choppy_output.mp4", help="Path to output video")
    parser.add_argument("-f", "--fps", type=int, default=10, help="Target FPS (default: 10)")
    
    args = parser.parse_args()
    
    create_choppy_video(args.input_video, args.output, args.fps)
