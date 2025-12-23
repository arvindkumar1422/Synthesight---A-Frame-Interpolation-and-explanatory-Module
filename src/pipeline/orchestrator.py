import cv2
import numpy as np
import time
import json
import logging
import os
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

from src.interpolation.engine import SmartInterpolator
from src.detection.metrics import ArtifactDetector
from src.explanation.generator import ExplanationGenerator

class PipelineOrchestrator:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.console = Console()
        
        with self.console.status("[bold green]Initializing AI Models..."):
            self.interpolator = SmartInterpolator(config)
            self.detector = ArtifactDetector(config)
            self.explainer = ExplanationGenerator(config)

    def process_video(self, input_path, output_path, report_path):
        self.console.print(f"[bold blue]SYNTHESIGHT[/bold blue] Processing: [underline]{input_path}[/underline]")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Output video writer (2x FPS for 2x interpolation)
        fourcc = cv2.VideoWriter_fourcc(*self.config['output']['video_codec'])
        out = cv2.VideoWriter(output_path, fourcc, fps * 2, (width, height))

        report_data = []
        
        ret, prev_frame = cap.read()
        if not ret:
            return

        # Write first frame
        out.write(prev_frame)
        
        # Setup Rich Progress
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        
        task_id = progress.add_task("[cyan]Interpolating...", total=total_frames-1)
        
        frame_idx = 0
        
        # Live Dashboard
        layout = Layout()
        layout.split_column(
            Layout(name="progress", size=3),
            Layout(name="metrics")
        )
        layout["progress"].update(Panel(progress, title="Progress", border_style="green"))
        
        # Create debug directory for dashboard
        os.makedirs("debug_frames", exist_ok=True)

        with Live(layout, refresh_per_second=4) as live:
            while True:
                ret, curr_frame = cap.read()
                if not ret:
                    break

                # Interpolate
                start_time = time.time()
                prev_rgb = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2RGB)
                curr_rgb = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2RGB)
                
                interp_rgb = self.interpolator.interpolate(prev_rgb, curr_rgb, 0.5)
                interp_bgr = cv2.cvtColor(interp_rgb, cv2.COLOR_RGB2BGR)
                inference_time = time.time() - start_time

                # Detect Artifacts
                metrics = self.detector.detect_artifacts(prev_frame, curr_frame, interp_bgr)
                
                # Explain
                explanation = self.explainer.generate_explanation(metrics)
                
                # Save debug frames for dashboard (Optimized)
                save_debug = self.config['explanation'].get('save_debug_frames', False)
                interval = self.config['explanation'].get('debug_save_interval', 1)
                should_save = save_debug and (frame_idx % interval == 0)
                
                paths = {}
                if should_save:
                    debug_base = f"debug_frames/frame_{frame_idx}"
                    cv2.imwrite(f"{debug_base}_prev.jpg", prev_frame)
                    cv2.imwrite(f"{debug_base}_interp.jpg", interp_bgr)
                    cv2.imwrite(f"{debug_base}_next.jpg", curr_frame)
                    
                    paths["prev"] = f"{debug_base}_prev.jpg"
                    paths["interp"] = f"{debug_base}_interp.jpg"
                    paths["next"] = f"{debug_base}_next.jpg"
                    
                    # Visual Explanation (Heatmap)
                    if self.config['explanation'].get('generate_heatmaps', True):
                        heatmap = self.explainer.generate_heatmap(interp_bgr, metrics)
                        if heatmap is not None:
                             cv2.imwrite(f"{debug_base}_heatmap.jpg", heatmap)
                             paths["heatmap"] = f"{debug_base}_heatmap.jpg"

                # Log data
                frame_report = {
                    "frame_pair": frame_idx,
                    "metrics": metrics,
                    "explanation": explanation,
                    "inference_time": inference_time,
                    "paths": paths
                }
                report_data.append(frame_report)

                # Write frames
                out.write(interp_bgr)
                out.write(curr_frame)

                prev_frame = curr_frame
                frame_idx += 1
                progress.update(task_id, advance=1)
                
                # Update Dashboard Metrics
                table = Table(title=f"Frame {frame_idx} Analysis")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="magenta")
                table.add_row("Motion", f"{metrics['motion_complexity']:.2f}")
                table.add_row("Consistency", f"{metrics['temporal_consistency']:.2f}")
                table.add_row("Occlusion Risk", f"{metrics['occlusion_risk']:.2f}")
                table.add_row("Verdict", explanation['verdict'], style="red" if explanation['verdict'] == "FAIL" else "green")
                
                layout["metrics"].update(Panel(table, title="Real-time Analysis", border_style="blue"))

        cap.release()
        out.release()

        # Save report
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.console.print(f"[bold green]Success![/bold green] Output saved to {output_path}")
        self.console.print(f"Report saved to {report_path}")
