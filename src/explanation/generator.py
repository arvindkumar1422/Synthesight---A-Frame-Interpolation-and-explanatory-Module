import cv2
import numpy as np

class ExplanationGenerator:
    def __init__(self, config=None):
        self.config = config

    def generate_heatmap(self, frame, metrics):
        """
        Generate a visual heatmap overlay indicating potential artifact regions.
        For MVP, we use edge difference as a proxy for artifact location.
        """
        # Create a dummy heatmap based on edge intensity (placeholder for real uncertainty map)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # Blur to create a "heat" effect
        heatmap = cv2.GaussianBlur(edges, (21, 21), 0)
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # Overlay
        alpha = 0.4
        overlay = cv2.addWeighted(frame, 1 - alpha, heatmap, alpha, 0)
        return overlay

    def generate_explanation(self, metrics):
        """
        Generate a text explanation based on artifact metrics.
        """
        explanations = []
        severity_score = 0.0
        
        # Motion Analysis
        motion = metrics.get("motion_complexity", 0)
        if motion > 5.0:
            explanations.append(f"High motion detected (magnitude: {motion:.2f}). This increases the risk of occlusion artifacts.")
            severity_score += 0.4
        elif motion > 2.0:
            explanations.append(f"Moderate motion detected (magnitude: {motion:.2f}).")
            severity_score += 0.1
        else:
            explanations.append("Low motion scene. Interpolation should be reliable.")

        # Consistency Analysis
        consistency = metrics.get("temporal_consistency", 1.0)
        if consistency < 0.8:
            explanations.append(f"Low temporal consistency ({consistency:.2f}). The interpolated frame deviates significantly from its neighbors, suggesting potential warping or structural errors.")
            severity_score += 0.5
        
        # Edge/Blur Analysis
        edge_pres = metrics.get("edge_preservation", 1.0)
        if edge_pres < 0.8:
            explanations.append(f"Reduced edge density ({edge_pres:.2f}). The frame may suffer from blurring or ghosting.")
            severity_score += 0.3
        elif edge_pres > 1.2:
            explanations.append(f"Increased edge density ({edge_pres:.2f}). Potential high-frequency noise or artifacts introduced.")
            severity_score += 0.2

        # Occlusion Risk
        occ_risk = metrics.get("occlusion_risk", 0)
        if occ_risk > 20.0: # Arbitrary threshold for pixel diff
             explanations.append(f"High occlusion risk detected (diff: {occ_risk:.2f}).")
             severity_score += 0.3

        # Final Verdict
        severity_score = min(severity_score, 1.0)
        verdict = "PASS"
        if severity_score > 0.7:
            verdict = "FAIL"
        elif severity_score > 0.4:
            verdict = "WARNING"

        return {
            "verdict": verdict,
            "severity": severity_score,
            "details": explanations
        }
