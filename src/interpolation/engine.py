import numpy as np
import cv2
import logging
from abc import ABC, abstractmethod

# Try importing TensorFlow, but handle failure gracefully
try:
    import tensorflow as tf
    import tensorflow_hub as hub
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("Warning: TensorFlow not found. Falling back to linear interpolation.")

class BaseInterpolator(ABC):
    @abstractmethod
    def interpolate(self, frame1, frame2, time=0.5):
        pass

class LinearInterpolator(BaseInterpolator):
    """Fallback interpolator using simple linear blending."""
    def interpolate(self, frame1, frame2, time=0.5):
        return cv2.addWeighted(frame1, 1.0 - time, frame2, time, 0)

class FILMInterpolator(BaseInterpolator):
    def __init__(self, model_path):
        self.logger = logging.getLogger(__name__)
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is not available. Cannot use FILM.")
            
        self.logger.info(f"Loading FILM model from {model_path}...")
        try:
            # Load model
            self.model = hub.load(model_path)
            self.logger.info("FILM model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load FILM model: {e}")
            raise

    def _preprocess_frame(self, frame):
        frame = tf.image.convert_image_dtype(frame, tf.float32)
        frame = tf.expand_dims(frame, 0)
        return frame

    def _postprocess_frame(self, frame):
        frame = tf.clip_by_value(frame[0], 0.0, 1.0)
        frame = tf.image.convert_image_dtype(frame, tf.uint8)
        return frame.numpy()

    def interpolate(self, frame1, frame2, time=0.5):
        input_frame1 = self._preprocess_frame(frame1)
        input_frame2 = self._preprocess_frame(frame2)
        
        inputs = {
            'x0': input_frame1,
            'x1': input_frame2,
            'time': tf.expand_dims(tf.constant([time], dtype=tf.float32), axis=-1)
        }
        
        result = self.model(inputs, training=False)
        return self._postprocess_frame(result['image'])

class SmartInterpolator(BaseInterpolator):
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Try to initialize FILM, fallback to Linear if fails
        try:
            self.engine = FILMInterpolator(config['interpolation']['model_path'])
            self.logger.info("Using FILM Interpolation Engine")
        except Exception as e:
            self.logger.warning(f"Could not initialize FILM engine ({e}). Using Linear Fallback.")
            self.engine = LinearInterpolator()
            
        self.scene_change_threshold = config['detection']['thresholds']['scene_change_diff']

    def _detect_scene_change(self, frame1, frame2):
        """
        Detect if there is a scene cut between frame1 and frame2.
        Uses histogram comparison.
        """
        # Convert to HSV for better color comparison
        hsv1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2HSV)
        hsv2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2HSV)
        
        # Calculate histograms (H and S channels)
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [180, 256], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [180, 256], [0, 180, 0, 256])
        
        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
        
        # Compare histograms (Correlation)
        # 1.0 is perfect match, < 0.5 usually means different scene
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # If similarity is low, it's a scene change
        # We invert logic: return True if change detected
        # scene_change_diff is typically 0.3, so threshold is 0.7
        # If similarity < 0.7, it is a cut.
        threshold = 1.0 - self.scene_change_threshold
        is_cut = similarity < threshold
        return is_cut, similarity

    def interpolate(self, frame1, frame2, time=0.5):
        """
        Smart interpolation that checks for scene cuts.
        """
        is_cut, score = self._detect_scene_change(frame1, frame2)
        
        if is_cut:
            self.logger.warning(f"Scene cut detected (similarity: {score:.2f}). Skipping interpolation to avoid morphing.")
            # Return frame1 or frame2 (duplicate) instead of morphing
            # For t=0.5, we can just return frame1 or frame2. Let's return frame1 for first half, frame2 for second.
            if time < 0.5:
                return frame1
            else:
                return frame2
        
        # If no cut, proceed with heavy interpolation
        return self.engine.interpolate(frame1, frame2, time)

    def interpolate(self, frame1, frame2, time=0.5):
        """
        Smart interpolation that checks for scene cuts.
        """
        is_cut, score = self._detect_scene_change(frame1, frame2)
        
        if is_cut:
            self.logger.warning(f"Scene cut detected (similarity: {score:.2f}). Skipping interpolation to avoid morphing.")
            # Return frame1 or frame2 (duplicate) instead of morphing
            # For t=0.5, we can just return frame1 or frame2. Let's return frame1 for first half, frame2 for second.
            if time < 0.5:
                return frame1
            else:
                return frame2
        
        # If no cut, proceed with heavy interpolation
        return self.engine.interpolate(frame1, frame2, time)
