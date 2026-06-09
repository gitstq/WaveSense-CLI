"""
Phase-Based Motion Detector
基于相位的运动检测器

Detects motion by analyzing phase changes across CSI subcarriers.
Motion causes phase shifts that are more sensitive than amplitude changes.
"""

import math
import statistics
from typing import Dict, List, Optional, Deque
from collections import deque
from .amplitude_detector import DetectionResult


class PhaseDetector:
    """
    Detect motion using phase variation analysis.
    
    Phase is more sensitive to small movements than amplitude,
    making this detector suitable for subtle motion detection.
    """

    def __init__(
        self,
        threshold: float = 0.3,
        adaptation_rate: float = 0.03,
        min_duration: int = 2,
        history_size: int = 50
    ):
        self.threshold = threshold
        self.adaptation_rate = adaptation_rate
        self.min_duration = min_duration
        self.history_size = history_size

        self._history: Deque[float] = deque(maxlen=history_size)
        self._adaptive_threshold = threshold
        self._consecutive_detections = 0
        self._last_phase: Optional[List[float]] = None

    def detect(self, features: Dict) -> DetectionResult:
        """Detect motion from phase features"""
        timestamp = features.get("timestamp", 0.0)
        phase = features.get("phase", [])
        ph_variance = features.get("phase_variance", 0.0)

        if not phase:
            return DetectionResult(
                timestamp=timestamp,
                motion_detected=False,
                confidence=0.0,
                detector_type="phase",
                details={"error": "No phase data"}
            )

        # Calculate phase difference
        if self._last_phase is not None:
            # Use circular distance for phase
            diff = []
            for p1, p2 in zip(phase, self._last_phase):
                d = abs(p1 - p2)
                # Handle phase wrapping
                while d > math.pi:
                    d = abs(d - 2 * math.pi)
                diff.append(d)
            mean_diff = statistics.mean(diff) if diff else 0.0
        else:
            mean_diff = 0.0

        self._last_phase = list(phase)

        # Update history
        self._history.append(mean_diff)

        # Update adaptive threshold
        if len(self._history) >= 10:
            hist_mean = statistics.mean(self._history)
            hist_std = statistics.stdev(self._history) if len(self._history) > 1 else 0.0
            target_threshold = hist_mean + 2.5 * hist_std
            self._adaptive_threshold += self.adaptation_rate * (
                target_threshold - self._adaptive_threshold
            )

        # Detection
        is_anomaly = mean_diff > self._adaptive_threshold

        if is_anomaly:
            self._consecutive_detections += 1
        else:
            self._consecutive_detections = 0

        motion_detected = self._consecutive_detections >= self.min_duration

        # Confidence
        if motion_detected:
            confidence = min(1.0, mean_diff / (self._adaptive_threshold * 2.0))
        else:
            confidence = min(1.0, mean_diff / self._adaptive_threshold) if self._adaptive_threshold > 0 else 0.0

        return DetectionResult(
            timestamp=timestamp,
            motion_detected=motion_detected,
            confidence=confidence,
            detector_type="phase",
            details={
                "mean_diff": mean_diff,
                "variance": ph_variance,
                "threshold": self._adaptive_threshold,
                "consecutive": self._consecutive_detections
            }
        )

    def reset(self) -> None:
        """Reset detector state"""
        self._history.clear()
        self._adaptive_threshold = self.threshold
        self._consecutive_detections = 0
        self._last_phase = None
