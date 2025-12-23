import cv2
import argparse
import sys
import os
import numpy as np

def create_choppy_video(input_path, output_path, keep_every_n_frames=3):
    """
    Creates a choppy (low FPS) video from a smooth video by dropping frames.
    
    Args:
        input_path: Path to source video.
        output_path: Path to save degraded video.
        keep_every_n_frames: Decimation factor. 
                             e.g., 3 means keep frame 0, 3, 6... (30fps -> 10fps)
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video source {input_path}")
        return

    # Get video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Calculate new FPS
    new_fps = original_fps / keep_every_n_frames
    
    print(f"--- Video Degrader ---")
    print(f"Input:  {input_path}")
    print(f"  FPS: {original_fps}")
    print(f"  Frames: {total_frames}")
    print(f"  Duration: {total_frames/original_fps:.2f}s")
    print(f"----------------------")
    print(f"Degrading by factor of {keep_every_n_frames}...")
    print(f"Target FPS: {new_fps:.2f}")

    # Initialize writer
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_path, fourcc, new_fps, (width, height))

    frame_idx = 0
    kept_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Keep only every Nth frame
        if frame_idx % keep_every_n_frames == 0:
            out.write(frame)
            kept_count += 1
        
        frame_idx += 1

    cap.release()
    out.release()
    
    print(f"----------------------")
    print(f"Success! Saved to {output_path}")
    print(f"Kept {kept_count} frames.")
    print(f"New Duration: {kept_count/new_fps:.2f}s (should match original)")

def generate_synthetic_smooth_video(output_path, duration=5, fps=30, width=640, height=480):
    """
    Generates a synthetic smooth video of a moving circle for testing.
    """
    print(f"Generating synthetic smooth video: {output_path}...")
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    # Ball properties
    radius = 30
    color = (0, 255, 0) # Green
    x, y = width // 2, height // 2
    speed_x = 5
    speed_y = 3
    
    for i in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Move ball
        x += speed_x
        y += speed_y
        
        # Bounce
        if x - radius < 0 or x + radius > width:
            speed_x = -speed_x
        if y - radius < 0 or y + radius > height:
            speed_y = -speed_y
            
        # Draw
        cv2.circle(frame, (x, y), radius, color, -1)
        
        # Add text
        cv2.putText(frame, f"Frame: {i}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
        
    out.release()
    print("Synthetic video generation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a choppy/laggy video from a smooth one.")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Degrade command
    degrade_parser = subparsers.add_parser('degrade', help='Degrade an existing video')
    degrade_parser.add_argument("input", help="Input smooth video path")
    degrade_parser.add_argument("--output", "-o", default="choppy_output.mp4", help="Output video path")
    degrade_parser.add_argument("--factor", "-f", type=int, default=3, help="Decimation factor (e.g. 3 keeps 1/3 frames)")

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate a synthetic smooth video first')
    gen_parser.add_argument("--output", "-o", default="smooth_synthetic.mp4", help="Output path")
    
    args = parser.parse_args()
    
    if args.command == 'degrade':
        create_choppy_video(args.input, args.output, args.factor)
    elif args.command == 'generate':
        generate_synthetic_smooth_video(args.output)
    else:
        parser.print_help()
