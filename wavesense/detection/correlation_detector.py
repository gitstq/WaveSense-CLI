"""
Subcarrier Correlation Motion Detector
子载波相关性运动检测器

Detects motion by measuring correlation degradation between
consecutive CSI samples across subcarriers.
"""

import statistics
from typing import Dict, List, Optional, Deque
from collections import deque
from .amplitude_detector import DetectionResult


class CorrelationDetector:
    """
    Detect motion using subcarrier correlation analysis.
    
    When motion occurs, the correlation between consecutive CSI
    samples decreases due to channel perturbations.
    """

    def __init__(
        self,
        threshold: float = 0.85,
        adaptation_rate: float = 0.02,
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
        self._last_amplitude: Optional[List[float]] = None

    def detect(self, features: Dict) -> DetectionResult:
        """Detect motion from correlation features"""
        timestamp = features.get("timestamp", 0.0)
        amplitude = features.get("amplitude", [])

        if not amplitude or self._last_amplitude is None:
            self._last_amplitude = list(amplitude) if amplitude else None
            return DetectionResult(
                timestamp=timestamp,
                motion_detected=False,
                confidence=0.0,
                detector_type="correlation",
                details={"status": "initializing"}
            )

        # Calculate Pearson correlation
        correlation = self._calculate_correlation(amplitude, self._last_amplitude)
        self._last_amplitude = list(amplitude)

        # Correlation degradation (1.0 = perfect, 0.0 = no correlation)
        degradation = 1.0 - abs(correlation)

        # Update history
        self._history.append(degradation)

        # Update adaptive threshold
        if len(self._history) >= 10:
            hist_mean = statistics.mean(self._history)
            hist_std = statistics.stdev(self._history) if len(self._history) > 1 else 0.0
            target_threshold = hist_mean + 2.0 * hist_std
            self._adaptive_threshold += self.adaptation_rate * (
                target_threshold - self._adaptive_threshold
            )

        # Detection (degradation above threshold indicates motion)
        is_anomaly = degradation > self._adaptive_threshold

        if is_anomaly:
            self._consecutive_detections += 1
        else:
            self._consecutive_detections = 0

        motion_detected = self._consecutive_detections >= self.min_duration

        # Confidence
        if motion_detected:
            confidence = min(1.0, degradation / (self._adaptive_threshold * 1.5))
        else:
            confidence = min(1.0, degradation / self._adaptive_threshold) if self._adaptive_threshold > 0 else 0.0

        return DetectionResult(
            timestamp=timestamp,
            motion_detected=motion_detected,
            confidence=confidence,
            detector_type="correlation",
            details={
                "correlation": correlation,
                "degradation": degradation,
                "threshold": self._adaptive_threshold,
                "consecutive": self._consecutive_detections
            }
        )

    def _calculate_correlation(
        self,
        a: List[float],
        b: List[float]
    ) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(a) != len(b) or len(a) == 0:
            return 1.0

        n = len(a)
        mean_a = statistics.mean(a)
        mean_b = statistics.mean(b)

        numerator = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
        denom_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
        denom_b = sum((y - mean_b) ** 2 for y in b) ** 0.5

        if denom_a == 0 or denom_b == 0:
            return 1.0

        return max(-1.0, min(1.0, numerator / (denom_a * denom_b)))

    def reset(self) -> None:
        """Reset detector state"""
        self._history.clear()
        self._adaptive_threshold = self.threshold
        self._consecutive_detections = 0
        self._last_amplitude = None
