"""
Unit tests for Detection module
检测模块单元测试
"""

import unittest
import time
from wavesense.detection.amplitude_detector import AmplitudeDetector
from wavesense.detection.phase_detector import PhaseDetector
from wavesense.detection.correlation_detector import CorrelationDetector
from wavesense.detection.fusion_engine import FusionEngine


class TestAmplitudeDetector(unittest.TestCase):
    """Test amplitude-based detector"""

    def test_no_motion(self):
        """Test with stable amplitude (no motion)"""
        detector = AmplitudeDetector(threshold=0.5)
        
        # Stable amplitude
        for _ in range(10):
            features = {
                "timestamp": time.time(),
                "amplitude": [1.0] * 64,
                "amplitude_variance": 0.01
            }
            result = detector.detect(features)
        
        self.assertFalse(result.motion_detected)

    def test_motion_detection(self):
        """Test with varying amplitude (motion)"""
        detector = AmplitudeDetector(threshold=0.1, min_duration=2)
        
        # Stable first
        for i in range(5):
            features = {
                "timestamp": time.time(),
                "amplitude": [1.0] * 64,
                "amplitude_variance": 0.01
            }
            detector.detect(features)
        
        # Then varying (motion)
        for i in range(5):
            features = {
                "timestamp": time.time(),
                "amplitude": [1.0 + i * 0.3] * 64,
                "amplitude_variance": 0.5
            }
            result = detector.detect(features)
        
        self.assertTrue(result.motion_detected)

    def test_confidence_range(self):
        """Test confidence is in valid range"""
        detector = AmplitudeDetector()
        
        features = {
            "timestamp": time.time(),
            "amplitude": [1.0] * 64,
            "amplitude_variance": 0.1
        }
        result = detector.detect(features)
        
        self.assertTrue(0.0 <= result.confidence <= 1.0)


class TestFusionEngine(unittest.TestCase):
    """Test fusion engine"""

    def test_majority_vote(self):
        """Test majority voting"""
        fusion = FusionEngine(method="majority_vote", confirmation_frames=1)
        
        from wavesense.detection.amplitude_detector import DetectionResult
        
        results = [
            DetectionResult(time.time(), True, 0.8, "amplitude", {}),
            DetectionResult(time.time(), True, 0.7, "phase", {}),
            DetectionResult(time.time(), False, 0.3, "correlation", {}),
        ]
        
        fused = fusion.fuse(results)
        self.assertTrue(fused.motion_detected)

    def test_sequential_fusion(self):
        """Test sequential fusion (all must agree)"""
        fusion = FusionEngine(method="sequential", confirmation_frames=1)
        
        from wavesense.detection.amplitude_detector import DetectionResult
        
        results = [
            DetectionResult(time.time(), True, 0.8, "amplitude", {}),
            DetectionResult(time.time(), True, 0.7, "phase", {}),
            DetectionResult(time.time(), True, 0.9, "correlation", {}),
        ]
        
        fused = fusion.fuse(results)
        self.assertTrue(fused.motion_detected)


if __name__ == "__main__":
    unittest.main()
