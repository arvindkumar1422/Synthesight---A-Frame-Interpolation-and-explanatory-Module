import cv2
import os
import argparse
import webbrowser

def inspect_videos(report_path=None):
    # Define files to inspect
    files = ["my_video.mp4", "my_choppy_video.mp4", "my_restored_pass1.mp4", "my_restored_final.mp4", "my_video_2x.mp4", "my_video_4x.mp4"]
    
    # Header for terminal
    print(f"{'Filename':<25} | {'FPS':<10} | {'Frames':<10} | {'Duration (s)':<10}")
    print("-" * 65)
    
    stats_html = """
    <div style="background: #222; padding: 20px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #444;">
        <h2 style="color: #4facfe; margin-top: 0;">Experiment Summary</h2>
        <table style="width: 100%; border-collapse: collapse; color: #eee; font-family: monospace;">
            <tr style="background: #333; text-align: left;">
                <th style="padding: 10px;">Filename</th>
                <th style="padding: 10px;">FPS</th>
                <th style="padding: 10px;">Frames</th>
                <th style="padding: 10px;">Duration (s)</th>
            </tr>
    """
    
    video_gallery_html = """
    <div style="background: #222; padding: 20px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #444;">
        <h2 style="color: #4facfe; margin-top: 0;">Video Results</h2>
        <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
    """

    for f in files:
        if not os.path.exists(f):
            # print(f"{f:<25} | NOT FOUND")
            continue
            
        cap = cv2.VideoCapture(f)
        if not cap.isOpened():
            print(f"{f:<25} | ERROR OPENING")
            continue
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frames / fps if fps > 0 else 0
        
        # Print to terminal
        print(f"{f:<25} | {fps:<10.2f} | {frames:<10} | {duration:<10.2f}")
        
        # Add to HTML Stats
        stats_html += f"""
            <tr style="border-bottom: 1px solid #444;">
                <td style="padding: 8px;">{f}</td>
                <td style="padding: 8px;">{fps:.2f}</td>
                <td style="padding: 8px;">{frames}</td>
                <td style="padding: 8px;">{duration:.2f}</td>
            </tr>
        """
        
        # Add to Video Gallery
        video_gallery_html += f"""
             <div style="width: 320px; background: #333; padding: 10px; border-radius: 5px;">
                <h4 style="color: #eee; margin: 0 0 10px 0; font-size: 14px; text-align: center;">{f} ({fps:.1f} FPS)</h4>
                <video width="320" height="180" controls style="width: 100%; border-radius: 4px;">
                    <source src="{f}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
             </div>
        """
        
        cap.release()

    stats_html += """
        </table>
    </div>
    """
    
    video_gallery_html += """
        </div>
    </div>
    """
    
    # Combine content to inject
    injected_content = stats_html + video_gallery_html

    # Inject into report if provided
    if report_path and os.path.exists(report_path):
        try:
            with open(report_path, 'r') as f:
                content = f.read()
            
            # Insert after the <body> tag or before the first container
            if "<body>" in content:
                # Insert after the title/header
                # We look for the h3 tag which is the subtitle
                split_point = "</h3>"
                if split_point in content:
                    parts = content.split(split_point, 1)
                    new_content = parts[0] + split_point + injected_content + parts[1]
                else:
                    # Fallback: insert after body
                    new_content = content.replace("<body>", "<body>" + injected_content)
                
                with open(report_path, 'w') as f:
                    f.write(new_content)
                
                print(f"\n[SUCCESS] Injected summary stats into {report_path}")
                
                # Open in browser
                abs_path = os.path.abspath(report_path)
                webbrowser.open(f"file://{abs_path}")
                print(f"[INFO] Opened report in default browser.")
                
        except Exception as e:
            print(f"\n[ERROR] Failed to inject stats into report: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--inject-report", help="Path to HTML report to inject stats into")
    args = parser.parse_args()
    
    inspect_videos(args.inject_report)
