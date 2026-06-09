"""
CSI Data Preprocessor
CSI数据预处理模块

Provides filtering, normalization, and feature extraction for raw CSI data.
提供滤波、归一化和特征提取功能。
"""

import math
import statistics
from typing import List, Dict, Optional, Callable
from collections import deque
from .csi_reader import CSIData


class CSIPreprocessor:
    """
    Preprocessor for CSI data streams.
    Applies filtering and normalization to improve detection accuracy.
    """

    def __init__(
        self,
        window_size: int = 10,
        filter_type: str = "median",
        normalize: bool = True
    ):
        self.window_size = window_size
        self.filter_type = filter_type
        self.normalize = normalize
        self._amplitude_buffer: deque = deque(maxlen=window_size)
        self._phase_buffer: deque = deque(maxlen=window_size)
        self._baseline: Optional[List[float]] = None

    def process(self, csi: CSIData) -> Dict:
        """
        Process a single CSI packet and extract features.
        
        Returns:
            Dict containing processed features:
            - amplitude: Filtered amplitude values
            - phase: Filtered phase values
            - amplitude_variance: Variance across subcarriers
            - phase_variance: Phase change variance
            - rssi: Signal strength
            - timestamp: Packet timestamp
        """
        amp = csi.amplitude
        ph = csi.phase

        # Update buffers
        self._amplitude_buffer.append(amp)
        self._phase_buffer.append(ph)

        # Apply filtering
        if len(self._amplitude_buffer) >= 3:
            filtered_amp = self._apply_filter(list(self._amplitude_buffer))
            filtered_ph = self._apply_filter(list(self._phase_buffer))
        else:
            filtered_amp = amp
            filtered_ph = ph

        # Establish baseline from first few samples
        if self._baseline is None and len(self._amplitude_buffer) >= self.window_size:
            self._baseline = [statistics.mean(col) for col in zip(*self._amplitude_buffer)]

        # Normalize if baseline established
        if self.normalize and self._baseline:
            filtered_amp = [a / b if b > 0 else a
                          for a, b in zip(filtered_amp, self._baseline)]

        # Calculate variance features
        amp_variance = statistics.variance(filtered_amp) if len(filtered_amp) > 1 else 0.0
        ph_variance = statistics.variance(filtered_ph) if len(filtered_ph) > 1 else 0.0

        return {
            "amplitude": filtered_amp,
            "phase": filtered_ph,
            "amplitude_variance": amp_variance,
            "phase_variance": ph_variance,
            "rssi": csi.rssi,
            "timestamp": csi.timestamp,
            "num_subcarriers": len(amp)
        }

    def _apply_filter(self, buffer: List[List[float]]) -> List[float]:
        """Apply selected filter to multi-sample buffer"""
        if self.filter_type == "median":
            return [statistics.median(col) for col in zip(*buffer)]
        elif self.filter_type == "mean":
            return [statistics.mean(col) for col in zip(*buffer)]
        elif self.filter_type == "ewma":
            alpha = 0.3
            result = list(buffer[0])
            for sample in buffer[1:]:
                result = [alpha * s + (1 - alpha) * r
                         for s, r in zip(sample, result)]
            return result
        else:
            return buffer[-1]  # No filtering

    def reset(self) -> None:
        """Reset preprocessor state"""
        self._amplitude_buffer.clear()
        self._phase_buffer.clear()
        self._baseline = None


class FeatureExtractor:
    """
    Extract advanced features from CSI data for motion detection.
    从CSI数据中提取高级特征用于运动检测。
    """

    @staticmethod
    def amplitude_features(amplitude: List[float]) -> Dict:
        """Extract amplitude-based features"""
        if not amplitude:
            return {}

        return {
            "mean": statistics.mean(amplitude),
            "std": statistics.stdev(amplitude) if len(amplitude) > 1 else 0.0,
            "max": max(amplitude),
            "min": min(amplitude),
            "range": max(amplitude) - min(amplitude),
        }

    @staticmethod
    def phase_features(phase: List[float]) -> Dict:
        """Extract phase-based features"""
        if not phase:
            return {}

        # Phase difference between adjacent subcarriers
        phase_diff = [phase[i+1] - phase[i] for i in range(len(phase)-1)]

        return {
            "mean": statistics.mean(phase),
            "std": statistics.stdev(phase) if len(phase) > 1 else 0.0,
            "diff_mean": statistics.mean(phase_diff) if phase_diff else 0.0,
            "diff_std": statistics.stdev(phase_diff) if len(phase_diff) > 1 else 0.0,
        }

    @staticmethod
    def subcarrier_correlation(
        current: List[float],
        previous: List[float]
    ) -> float:
        """
        Calculate correlation between current and previous CSI samples.
        Lower correlation indicates motion.
        """
        if not current or not previous or len(current) != len(previous):
            return 1.0

        n = len(current)
        mean_c = statistics.mean(current)
        mean_p = statistics.mean(previous)

        numerator = sum((c - mean_c) * (p - mean_p)
                       for c, p in zip(current, previous))
        denom_c = sum((c - mean_c) ** 2 for c in current) ** 0.5
        denom_p = sum((p - mean_p) ** 2 for p in previous) ** 0.5

        if denom_c == 0 or denom_p == 0:
            return 1.0

        correlation = numerator / (denom_c * denom_p)
        return max(-1.0, min(1.0, correlation))
