import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import logging

class ArtifactDetector:
    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config

    def calculate_ssim(self, img1, img2):
        """
        Calculate Structural Similarity Index (SSIM).
        """
        # Convert to grayscale for SSIM
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        return ssim(gray1, gray2)

    def calculate_psnr(self, img1, img2):
        """
        Calculate Peak Signal-to-Noise Ratio (PSNR).
        """
        return psnr(img1, img2)

    def calculate_optical_flow_magnitude(self, img1, img2):
        """
        Calculate average optical flow magnitude to estimate motion complexity.
        """
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        flow = cv2.calcOpticalFlowFarneback(
            gray1, gray2, None, 
            0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        return np.mean(magnitude)

    def estimate_occlusion(self, img1, img2):
        """
        Estimate occlusion area by checking forward-backward flow consistency.
        Simplified: Check difference between warped image and target.
        For MVP: Just return the pixel difference between frames as a proxy for change/occlusion risk.
        """
        diff = cv2.absdiff(img1, img2)
        return np.mean(diff)

    def detect_artifacts(self, original_prev, original_next, interpolated):
        """
        Run a suite of checks to detect potential artifacts.
        """
        
        # 1. Motion Complexity
        motion_mag = self.calculate_optical_flow_magnitude(original_prev, original_next)
        
        # 2. Temporal Consistency (simplified)
        # Compare interpolated frame to the average of prev and next
        avg_frame = cv2.addWeighted(original_prev, 0.5, original_next, 0.5, 0)
        consistency_score = self.calculate_ssim(interpolated, avg_frame)
        
        # 3. Edge Analysis (Ghosting detection)
        edges_prev = cv2.Canny(original_prev, 100, 200)
        edges_next = cv2.Canny(original_next, 100, 200)
        edges_interp = cv2.Canny(interpolated, 100, 200)
        
        edge_density_orig = (np.sum(edges_prev) + np.sum(edges_next)) / 2
        edge_density_interp = np.sum(edges_interp)
        edge_preservation = edge_density_interp / (edge_density_orig + 1e-6) 

        # 4. Occlusion Risk
        occlusion_risk = self.estimate_occlusion(original_prev, original_next)

        metrics = {
            "motion_complexity": float(motion_mag),
            "temporal_consistency": float(consistency_score),
            "edge_preservation": float(edge_preservation),
            "occlusion_risk": float(occlusion_risk)
        }
        
        return metrics
