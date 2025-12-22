# SYNTHESIGHT

Production-grade explainable frame interpolation system.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Interpolation**:
    ```bash
    python main.py path/to/your/video.mp4 -o output.mp4 -r report.json
    ```

## Architecture

-   **Interpolation**: Uses FILM (Frame Interpolation for Large Motion) via TensorFlow Hub.
-   **Detection**: Monitors Optical Flow, SSIM, and Edge Preservation to detect artifacts.
-   **Explanation**: Generates a JSON report with per-frame analysis and severity scores.

## Output

-   `output.mp4`: The 2x interpolated video.
-   `report.json`: Detailed frame-by-frame analysis of artifacts and explanations.
