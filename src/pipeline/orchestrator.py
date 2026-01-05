import cv2
import numpy as np
import time
import json
import logging
import os
import subprocess
from datetime import datetime
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

from src.interpolation.engine import SmartInterpolator
from src.detection.metrics import ArtifactDetector
from src.explanation.generator import ExplanationGenerator
from src.explanation.visualizer import AdvancedVisualizer
from src.explanation.report_generator import ReportGenerator

class PipelineOrchestrator:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.console = Console()
        
        with self.console.status("[bold green]Initializing AI Models..."):
            self.interpolator = SmartInterpolator(config)
            self.detector = ArtifactDetector(config)
            self.explainer = ExplanationGenerator(config)
            self.visualizer = AdvancedVisualizer(config)

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

        # Initialize Report Structure
        report_data = {
            "metadata": {
                "input_file": input_path,
                "output_file": output_path,
                "processing_date": datetime.now().isoformat(),
                "model_used": "FILM",
                "frame_rate_original": fps,
                "frame_rate_output": fps * 2,
                "total_frames_processed": total_frames
            },
            "summary": {
                "average_severity": 0.0,
                "verdict_distribution": {"PASS": 0, "WARNING": 0, "FAIL": 0},
                "processing_time_seconds": 0
            },
            "frames": []
        }
        
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
        start_process_time = time.time()
        
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
                
                # Smart Interpolator handles scene detection internally now
                interp_rgb = self.interpolator.interpolate(prev_rgb, curr_rgb, 0.5)
                interp_bgr = cv2.cvtColor(interp_rgb, cv2.COLOR_RGB2BGR)
                inference_time = time.time() - start_time

                # Detect Artifacts
                metrics = self.detector.detect_artifacts(prev_frame, curr_frame, interp_bgr)
                
                # Explain
                explanation = self.explainer.generate_explanation(metrics)
                
                # LLM Explanation (Advanced XAI)
                
                # Update Report
                frame_entry = {
                    "frame_number": frame_idx,
                    "timestamp": frame_idx / fps,
                    "metrics": metrics,
                    "severity_score": explanation['severity'],
                    "verdict": explanation['verdict'],
                    "explanation": explanation['details'],
                }
                report_data["frames"].append(frame_entry)
                report_data["summary"]["verdict_distribution"][explanation['verdict']] += 1
                
                # Save debug frames for dashboard (Optimized)
                save_debug = self.config['explanation'].get('save_debug_frames', False)
                if save_debug and explanation['verdict'] != "PASS":
                     # Use Advanced Visualizer for Composite XAI Frame
                     composite = self.visualizer.generate_composite_debug_frame(prev_frame, interp_bgr, metrics, explanation)
                     cv2.imwrite(f"debug_frames/frame_{frame_idx}_xai.jpg", composite)

                # Write frames (Interpolated + Next)
                out.write(interp_bgr)
                out.write(curr_frame)
                
                # Update Dashboard
                progress.update(task_id, advance=1)
                
                # Prepare next iteration
                prev_frame = curr_frame
                frame_idx += 1

        # Finalize Report
        end_process_time = time.time()
        report_data["summary"]["processing_time_seconds"] = end_process_time - start_process_time
        total_severity = sum(f["severity_score"] for f in report_data["frames"])
        if len(report_data["frames"]) > 0:
            report_data["summary"]["average_severity"] = total_severity / len(report_data["frames"])

        # Save Report
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        # Generate HTML Report
        html_path = report_path.replace(".json", ".html")
        try:
            gen = ReportGenerator(report_path)
            gen.generate_html_report(html_path)
            self.console.print(f"[bold green]HTML Report Generated: {html_path}[/bold green]")
        except Exception as e:
            self.logger.error(f"Failed to generate HTML report: {e}")
            
        out.release()
        cap.release()
        
        self.console.print("[bold green]Video Processing Complete![/bold green]")
        
        # Audio Transfer (if ffmpeg is available)
        self._transfer_audio(input_path, output_path)

    def _transfer_audio(self, input_path, output_path):
        """
        Transfers audio from input to output using ffmpeg.
        """
        try:
            temp_output = output_path.replace(".mp4", "_temp.mp4")
            os.rename(output_path, temp_output)
            
            # Use ffmpeg to copy video stream and audio stream
            # -shortest ensures output duration matches the shortest stream (video)
            # This fixes the duration mismatch issue
            cmd = [
                "ffmpeg", "-y",
                "-i", temp_output,
                "-i", input_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_path
            ]
            
            self.console.print("[yellow]Transferring Audio...[/yellow]")
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.remove(temp_output)
            self.console.print("[bold green]Audio Transferred Successfully![/bold green]")
            
        except Exception as e:
            self.logger.warning(f"Audio transfer failed (ffmpeg might be missing or input has no audio): {e}")
            # Restore original file if transfer failed
            if os.path.exists(temp_output):
                os.rename(temp_output, output_path)
