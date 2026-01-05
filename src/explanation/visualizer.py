import cv2
import numpy as np
import matplotlib.pyplot as plt
import io

class AdvancedVisualizer:
    def __init__(self, config=None):
        self.config = config

    def generate_composite_debug_frame(self, original, interpolated, metrics, explanation):
        """
        Generates a 2x2 composite frame for advanced debugging/XAI.
        Top-Left: Original Frame
        Top-Right: Interpolated Frame
        Bottom-Left: Motion Entropy Map (Optical Flow Magnitude)
        Bottom-Right: Error Confidence Map (Heatmap)
        """
        h, w = original.shape[:2]
        
        # 1. Motion Entropy Map (Visualizing Optical Flow)
        # We need to re-calculate flow here or pass it in. For efficiency, let's approximate
        # using the difference between original and interpolated as a proxy for motion/change
        # Ideally, we should pass the flow field from the detector, but for now:
        gray_orig = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        gray_interp = cv2.cvtColor(interpolated, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(gray_orig, gray_interp, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        # Normalize magnitude to 0-255 for visualization
        mag_norm = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
        mag_norm = mag_norm.astype(np.uint8)
        motion_map = cv2.applyColorMap(mag_norm, cv2.COLORMAP_VIRIDIS)
        
        # Add label
        cv2.putText(motion_map, f"Motion Entropy (Mc={metrics['motion_complexity']:.2f})", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 2. Error Confidence Map (Heatmap)
        # Re-use the logic from ExplanationGenerator but make it standalone here
        edges = cv2.Canny(gray_interp, 100, 200)
        heatmap_blur = cv2.GaussianBlur(edges, (21, 21), 0)
        error_map = cv2.applyColorMap(heatmap_blur, cv2.COLORMAP_JET)
        
        # Add label
        cv2.putText(error_map, f"Error Confidence (Severity={explanation['severity']:.2f})", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 3. Annotate Original and Interpolated
        orig_annotated = original.copy()
        cv2.putText(orig_annotated, "Original Frame (t)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        interp_annotated = interpolated.copy()
        cv2.putText(interp_annotated, "Interpolated Frame (t+0.5)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Combine into 2x2 Grid
        top_row = np.hstack((orig_annotated, interp_annotated))
        bottom_row = np.hstack((motion_map, error_map))
        composite = np.vstack((top_row, bottom_row))
        
        # Resize if too large (optional, for display)
        # composite = cv2.resize(composite, (w, h)) 
        
        return composite
