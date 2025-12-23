import argparse
import logging
import sys
import os
import yaml
from rich.logging import RichHandler

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

from src.pipeline.orchestrator import PipelineOrchestrator

def load_config(config_path="config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="SYNTHESIGHT: Explainable Frame Interpolation")
    parser.add_argument("input_video", help="Path to input video file")
    parser.add_argument("--output", "-o", default="output.mp4", help="Path to output video file")
    parser.add_argument("--report", "-r", default="report.json", help="Path to output report JSON")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to config file")
    
    args = parser.parse_args()

    if not os.path.exists(args.input_video):
        print(f"Error: Input file '{args.input_video}' not found.")
        sys.exit(1)

    try:
        config = load_config(args.config)
        # Override config with CLI args if needed
        
        orchestrator = PipelineOrchestrator(config)
        orchestrator.process_video(args.input_video, args.output, args.report)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
