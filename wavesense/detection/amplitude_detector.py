"""
Amplitude-Based Motion Detector
基于幅度的运动检测器

Detects motion by analyzing amplitude variations across CSI subcarriers.
通过分析CSI子载波的幅度变化来检测运动。
"""

import math
import statistics
from typing import Dict, List, Optional, Deque
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DetectionResult:
    """Motion detection result"""
    timestamp: float
    motion_detected: bool
    confidence: float
    detector_type: str
    details: Dict


class AmplitudeDetector:
    """
    Detect motion using amplitude difference analysis.
    
    Algorithm:
    1. Calculate amplitude variance across subcarriers
    2. Compare with adaptive threshold
    3. Apply temporal consistency check
    """

    def __init__(
        self,
        threshold: float = 0.15,
        adaptation_rate: float = 0.05,
        min_duration: int = 3,
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
        """
        Detect motion from preprocessed features.
        
        Args:
            features: Output from CSIPreprocessor.process()
        
        Returns:
            DetectionResult with motion status and confidence
        """
        timestamp = features.get("timestamp", 0.0)
        amplitude = features.get("amplitude", [])
        amp_variance = features.get("amplitude_variance", 0.0)

        if not amplitude:
            return DetectionResult(
                timestamp=timestamp,
                motion_detected=False,
                confidence=0.0,
                detector_type="amplitude",
                details={"error": "No amplitude data"}
            )

        # Calculate amplitude difference from last sample
        if self._last_amplitude is not None:
            diff = [abs(a - b) for a, b in zip(amplitude, self._last_amplitude)]
            mean_diff = statistics.mean(diff) if diff else 0.0
            max_diff = max(diff) if diff else 0.0
        else:
            mean_diff = 0.0
            max_diff = 0.0

        self._last_amplitude = list(amplitude)

        # Update history
        self._history.append(mean_diff)

        # Update adaptive threshold
        if len(self._history) >= 10:
            hist_mean = statistics.mean(self._history)
            hist_std = statistics.stdev(self._history) if len(self._history) > 1 else 0.0
            target_threshold = hist_mean + 2.0 * hist_std
            self._adaptive_threshold += self.adaptation_rate * (
                target_threshold - self._adaptive_threshold
            )

        # Detection logic
        is_anomaly = mean_diff > self._adaptive_threshold

        if is_anomaly:
            self._consecutive_detections += 1
        else:
            self._consecutive_detections = 0

        motion_detected = self._consecutive_detections >= self.min_duration

        # Calculate confidence
        if motion_detected:
            confidence = min(1.0, mean_diff / (self._adaptive_threshold * 2.0))
        else:
            confidence = min(1.0, mean_diff / self._adaptive_threshold) if self._adaptive_threshold > 0 else 0.0

        return DetectionResult(
            timestamp=timestamp,
            motion_detected=motion_detected,
            confidence=confidence,
            detector_type="amplitude",
            details={
                "mean_diff": mean_diff,
                "max_diff": max_diff,
                "variance": amp_variance,
                "threshold": self._adaptive_threshold,
                "consecutive": self._consecutive_detections
            }
        )

    def reset(self) -> None:
        """Reset detector state"""
        self._history.clear()
        self._adaptive_threshold = self.threshold
        self._consecutive_detections = 0
        self._last_amplitude = None
