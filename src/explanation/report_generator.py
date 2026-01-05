import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

class ReportGenerator:
    def __init__(self, report_path):
        self.report_path = report_path
        with open(report_path, 'r') as f:
            self.data = json.load(f)

    def generate_html_report(self, output_html_path):
        """
        Generates an interactive HTML report using Plotly.
        """
        frames = self.data['frames']
        if not frames:
            return

        df = pd.DataFrame([
            {
                'frame': f['frame_number'],
                'severity': f['severity_score'],
                'motion': f['metrics']['motion_complexity'],
                'consistency': f['metrics']['temporal_consistency'],
                'verdict': f['verdict']
            }
            for f in frames
        ])

        # Create Subplots
        fig = make_subplots(rows=3, cols=1, 
                            shared_xaxes=True, 
                            vertical_spacing=0.1,
                            subplot_titles=("Artifact Severity Score", "Motion Complexity", "Temporal Consistency"))

        # 1. Severity Score
        colors = {'PASS': 'green', 'WARNING': 'orange', 'FAIL': 'red'}
        marker_colors = [colors[v] for v in df['verdict']]
        
        fig.add_trace(go.Scatter(
            x=df['frame'], y=df['severity'],
            mode='lines+markers',
            name='Severity',
            marker=dict(color=marker_colors, size=6),
            line=dict(color='gray', width=1)
        ), row=1, col=1)

        # 2. Motion Complexity
        fig.add_trace(go.Scatter(
            x=df['frame'], y=df['motion'],
            mode='lines',
            name='Motion',
            line=dict(color='blue')
        ), row=2, col=1)

        # 3. Temporal Consistency
        fig.add_trace(go.Scatter(
            x=df['frame'], y=df['consistency'],
            mode='lines',
            name='Consistency',
            line=dict(color='purple')
        ), row=3, col=1)

        # Layout Updates
        fig.update_layout(
            title_text=f"SyntheSight Analysis Report: {self.data['metadata']['input_file']}",
            height=900,
            showlegend=False
        )
        
        # Add Verdict Zones to Severity Plot
        fig.add_hrect(y0=0.0, y1=0.3, row=1, col=1, fillcolor="green", opacity=0.1, layer="below", annotation_text="PASS")
        fig.add_hrect(y0=0.3, y1=0.7, row=1, col=1, fillcolor="orange", opacity=0.1, layer="below", annotation_text="WARNING")
        fig.add_hrect(y0=0.7, y1=1.0, row=1, col=1, fillcolor="red", opacity=0.1, layer="below", annotation_text="FAIL")

        # Save to HTML with embedded images script
        html_content = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Generate Image Gallery HTML
        gallery_html = """
        <div style="font-family: sans-serif; margin: 20px;">
            <h2>XAI Frame Inspector</h2>
            <p>Below are the Explainable AI debug frames for the analyzed video. Each frame shows the original input, the interpolated result, and the internal motion/error maps.</p>
            <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">
        """
        
        for f in frames:
            frame_idx = f['frame_number']
            verdict = f['verdict']
            severity = f['severity_score']
            
            # Check if image exists
            img_path = f"debug_frames/frame_{frame_idx}_xai.jpg"
            if os.path.exists(img_path):
                border_color = "green" if verdict == "PASS" else "orange" if verdict == "WARNING" else "red"
                gallery_html += f"""
                <div style="border: 2px solid {border_color}; padding: 5px; width: 320px; background: #f0f0f0; border-radius: 5px;">
                    <h4 style="margin: 5px 0;">Frame {frame_idx} <span style="float:right; color:{border_color}">{verdict}</span></h4>
                    <img src="{img_path}" style="width: 100%; display: block;" loading="lazy" onclick="window.open(this.src, '_blank');"/>
                    <p style="font-size: 12px; margin: 5px 0;"><b>Severity:</b> {severity:.2f}</p>
                    <details>
                        <summary style="font-size: 12px; cursor: pointer;">Explanation</summary>
                        <ul style="font-size: 11px; padding-left: 15px; margin: 5px 0;">
                            {''.join(f'<li>{e}</li>' for e in f['explanation'])}
                        </ul>
                    </details>
                </div>
                """
        
        gallery_html += """
            </div>
        </div>
        """
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SyntheSight Analysis Report</title>
            <style>
                body {{ margin: 0; padding: 20px; background-color: #111; color: #eee; }}
            </style>
        </head>
        <body>
            <h1 style="text-align: center; color: #4facfe;">SyntheSight Analysis Report</h1>
            <h3 style="text-align: center; color: #aaa;">{self.data['metadata']['input_file']}</h3>
            
            <!-- Plotly Graphs -->
            <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
                {html_content}
            </div>
            
            <!-- Image Gallery -->
            {gallery_html}
            
        </body>
        </html>
        """

        with open(output_html_path, 'w') as f:
            f.write(full_html)
            
        print(f"HTML Report generated: {output_html_path}")

if __name__ == "__main__":
    # Test
    gen = ReportGenerator("new_report.json")
    gen.generate_html_report("analysis_report.html")
